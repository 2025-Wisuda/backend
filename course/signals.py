"""
Signal handlers for CourseSessionModel and CourseSessionAttendanceModel.
Handles synchronization with LabSchedule aggregator for session scheduling,
automatic session completion when sessions become overdue, and
auto-generation of attendance records for enrolled students.

Soft deletes are handled by marking aggregator entries inactive.
"""

import logging

from core.enums import SessionStatus
from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import CourseModel, CourseSessionModel

logger = logging.getLogger("application.course")


@receiver(post_save, sender=CourseSessionModel)
def course_session_saved(sender, instance, created, **kwargs):
    """
    Handle CourseSession save event - synchronize with LabSchedule aggregator
    and auto-complete if overdue.

    This signal will:
    1. Sync the CourseSession to LabSchedule only if is_active is True and not cancelled.
    2. If is_active is False or status is cancelled, soft remove (set is_active=False) in aggregator.
    3. Auto-complete the session if it's overdue.
    """

    def sync_and_auto_complete():
        try:
            from lab_schedule.models import LabScheduleModel

            # Auto-complete if overdue
            if instance.auto_complete_if_overdue():
                logger.info(
                    f"Auto-completed overdue session: {instance.id} ({instance.type}) for course {instance.course.title}"
                )

            if instance.is_active and instance.status != SessionStatus.CANCELLED:
                action = "created" if created else "updated"
                logger.info(
                    f"CourseSession {action}: {instance.id} ({instance.type}) for course {instance.course.title}"
                )
                LabScheduleModel.sync_from_course_session(instance)
                logger.debug(
                    f"CourseSession signal: {instance.id} {action} at {timezone.localtime()}"
                )

                # Auto-generate attendance records for new sessions
                if created:
                    try:
                        from .models import CourseSessionAttendanceModel

                        records_created = (
                            CourseSessionAttendanceModel.bulk_generate_for_session(
                                instance
                            )
                        )
                        logger.info(
                            f"Auto-generated {records_created} attendance records for session "
                            f"'{instance.title}' (ID: {instance.id})"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to auto-generate attendance records for session "
                            f"'{instance.title}' (ID: {instance.id}): {str(e)}"
                        )
            else:
                logger.info(
                    f"CourseSession {instance.id} inactive or cancelled - marking inactive in aggregator"
                )
                LabScheduleModel.remove_course_session(instance.pk)

        except Exception as e:
            logger.exception(f"Error during course_session_saved signal: {e}")

    transaction.on_commit(sync_and_auto_complete)


@receiver(post_delete, sender=CourseSessionModel)
def course_session_deleted(sender, instance, **kwargs):
    """
    Handle CourseSession deletion event - soft remove from LabSchedule aggregator.

    Note:
        This only marks the aggregator entry as inactive, it does not physically delete it.
    """

    def remove_from_schedule():
        try:
            from lab_schedule.models import LabScheduleModel

            logger.info(
                f"CourseSession deleted: {instance.id}, marking inactive in aggregator"
            )
            LabScheduleModel.remove_course_session(instance.pk)
            logger.debug(
                f"CourseSession deletion signal: {instance.id} deleted at {timezone.localtime()}"
            )

        except Exception as e:
            logger.exception(f"Error during course_session_deleted signal: {e}")

    transaction.on_commit(remove_from_schedule)



# Course session attendance signals
@receiver(m2m_changed, sender=CourseModel.students.through)
def update_attendance_for_enrollment_changes(
    sender, instance, action, pk_set, **kwargs
):
    """
    Update attendance records when course enrollment changes.

    Business Logic:
    - When students are added to a course, create attendance records for existing sessions
    - When students are removed, log for audit purposes but preserve records
    - Only affects future sessions, not past sessions
    """
    if action == "post_add" and pk_set:

        def create_attendance_records():
            try:
                from .models import CourseSessionAttendanceModel

                # Get all future sessions for this course
                future_sessions = instance.sessions.filter(
                    date__gte=timezone.localtime().date()
                )

                records_created = 0
                for session in future_sessions:
                    session_records = (
                        CourseSessionAttendanceModel.bulk_generate_for_session(session)
                    )
                    records_created += session_records

                if records_created > 0:
                    logger.info(
                        f"Created {records_created} attendance records for {len(pk_set)} "
                        f"newly enrolled students in course '{instance.title}' "
                        f"across {future_sessions.count()} future sessions"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to create attendance records for newly enrolled students "
                    f"in course '{instance.title}': {str(e)}"
                )

        transaction.on_commit(create_attendance_records)

    elif action == "post_remove" and pk_set:

        def log_student_removal():
            try:
                # Log the removal but don't delete attendance records for audit purposes
                logger.info(
                    f"Students removed from course '{instance.title}'. "
                    f"Existing attendance records preserved for audit purposes."
                )

            except Exception as e:
                logger.error(
                    f"Error handling student removal from course '{instance.title}': {str(e)}"
                )

        transaction.on_commit(log_student_removal)


@receiver(post_save, sender=CourseModel)
def course_saved(sender, instance, created, **kwargs):
    """
    Handle Course save event - manage session activation/deactivation based on course status.
    
    When a course is soft-deleted (is_active=False), all its sessions are deactivated.
    When a course is reactivated (is_active=True), reactivate valid sessions (future dates).
    """
    def handle_course_activation_status():
        try:
            if not instance.is_active:
                # Deactivate all sessions for this course
                deactivated_count = CourseSessionModel.bulk_deactivate_with_sync(
                    course=instance
                )
                
                if deactivated_count > 0:
                    logger.info(
                        f"Course '{instance.title}' deactivated - "
                        f"deactivated {deactivated_count} related sessions"
                    )
            else:
                # Course is active - reactivate valid future sessions
                today = timezone.localtime().date()
                
                # Reactivate sessions that are still in the future
                activated_count = CourseSessionModel.bulk_activate_with_sync(
                    course=instance,
                    date__gte=today  # Only future sessions
                )
                
                if activated_count > 0:
                    logger.info(
                        f"Course '{instance.title}' reactivated - "
                        f"reactivated {activated_count} valid future sessions"
                    )
        except Exception as e:
            logger.exception(f"Error during course_saved signal: {e}")
    
    transaction.on_commit(handle_course_activation_status)
