"""
Course Session Model for Laboratory Management System.

Key Business Logic:
- Sessions must fall within course date range (start_date ≤ date ≤ end_date)
- Status transitions validated by SessionStatus enum rules
- Lab schedule integration via LabScheduleMixin for conflict detection
- Auto-completion for overdue scheduled sessions
- Lab schedules activate/deactivate based on session status changes
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core import BaseModel, LabScheduleMixin, SessionStatus, SessionType, UserGroup
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.db.models.manager import Manager


class CourseSessionModel(BaseModel, LabScheduleMixin):
    if TYPE_CHECKING:
        objects: Manager[CourseSessionModel]
    """
    Laboratory course session with status management and scheduling integration.

    Key Features:
    - Session scheduling within course date boundaries
    - Status lifecycle management with enum validation
    - Lab resource conflict detection via LabScheduleMixin
    - Automatic completion for overdue sessions

    Validation in clean():
    - Session date within course start_date and end_date range
    """

    # Custom field mappings for LabScheduleMixin integration
    SCHEDULE_DATE_FIELD = "date"
    START_TIME_FIELD = "start_time"
    END_TIME_FIELD = "end_time"

    course = models.ForeignKey(
        "CourseModel",
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name=_("Course"),
        help_text=_("The course this session belongs to"),
    )

    date = models.DateField(
        db_index=True,
        verbose_name=_("Session Date"),
        help_text=_("Date when the session is scheduled"),
    )

    start_time = models.TimeField(
        verbose_name=_("Session Start Time"),
        help_text=_("Start time of the course session"),
    )

    end_time = models.TimeField(
        verbose_name=_("Session End Time"),
        help_text=_("End time of the course session"),
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_("Session Title"),
        help_text=_("Title or topic of this session"),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Session Description"),
        help_text=_(
            "Detailed description of the session content, objectives, and activities"
        ),
    )

    type = models.CharField(
        max_length=20,
        choices=SessionType.choices(),
        default=SessionType.EXPERIMENT,
        db_index=True,
        verbose_name=_("Session Type"),
        help_text=_("Type of session/activity (Percobaan, Responsi, Tutorial, etc.)"),
    )

    teaching_assistants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="course_sessions",
        blank=True,
        limit_choices_to={"groups__name": UserGroup.LABORATORY_ASSISTANT.value},
        verbose_name=_("Session Teaching Assistants"),
        help_text=_("Teaching assistants assigned to this specific session"),
    )

    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices(),
        default=SessionStatus.SCHEDULED,
        db_index=True,
        verbose_name=_("Session Status"),
        help_text=_("Current status of the session"),
    )

    class Meta:
        db_table = "course_session"
        ordering = ["date", "start_time"]
        verbose_name = _("Course Session")
        verbose_name_plural = _("Course Sessions")

        # Business rule: unique sessions per course/date/time
        unique_together = [["course", "date", "start_time"]]

        indexes = [
            models.Index(fields=["date", "start_time", "end_time"]),
            models.Index(fields=["course", "date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def clean(self):
        """
        Session date range validation.

        Business Rules:
        - Session date must be within course date boundaries
        - Course start_date ≤ date ≤ course end_date
        - Cannot edit sessions that have already passed
        """
        super().clean()

        errors = {}

        # Check if trying to edit a session that has already passed
        if self.pk:  # Only for existing sessions (updates)
            from django.utils import timezone
            
            current_datetime = timezone.localtime()
            current_date = current_datetime.date()
            current_time = current_datetime.time()
            
            # If session date has passed completely
            if self.date < current_date:
                errors["date"] = _("Cannot edit session that has already passed. Session date: {}").format(
                    self.date
                )
            
            # If session is today and time has passed
            elif self.date == current_date and self.end_time and self.end_time < current_time:
                errors["end_time"] = _("Cannot edit session that has already ended. Session ended at: {}").format(
                    self.end_time.strftime('%H:%M')
                )

        if self.course and self.date:
            if self.course.start_date and self.date < self.course.start_date:
                errors["date"] = _("Session date cannot be before course start date.")
            elif self.course.end_date and self.date > self.course.end_date:
                errors["date"] = _("Session date cannot be after course end date.")

        if errors:
            raise ValidationError(errors)

    def change_status(self, new_status, user=None):
        """Change session status with enum validation."""
        current_status = SessionStatus(self.status)

        if current_status.can_transition_to(new_status):
            self.status = new_status
            if user:
                self.updated_by = user
            self.save()
            return True
        return False

    def auto_complete_if_overdue(self):
        """Auto-complete session if overdue (date has passed)."""

        today = timezone.localtime().date()

        # Only auto-complete scheduled sessions that are overdue
        if self.status == SessionStatus.SCHEDULED and self.date < today:

            self.status = SessionStatus.COMPLETED
            self.save(update_fields=["status", "updated_at"])
            return True

        return False

    @classmethod
    def auto_complete_overdue_sessions(cls):
        """Auto-complete all overdue sessions in bulk."""

        today = timezone.localtime().date()

        overdue_sessions = cls.objects.filter(
            status=SessionStatus.SCHEDULED, date__lt=today
        )

        count = overdue_sessions.count()
        if count > 0:
            overdue_sessions.update(
                status=SessionStatus.COMPLETED, updated_at=timezone.localtime()
            )

        return count

    def get_type(self):
        """Get activity type for lab schedule integration."""
        from core.enums import ActivityType

        return ActivityType.PRACTICUM

    def get_detail(self):
        """Get activity detail for lab schedule integration."""
        return f"{self.title}"
    
    def get_course(self):
        """Get the course associated with this session."""
        return f"{self.course.title}"

    @classmethod
    def bulk_update_with_sync(cls, queryset, **update_fields):
        """
        Bulk update course sessions and manually sync to lab schedule.

        This method performs bulk update and then manually syncs each affected
        session to the lab schedule aggregator since bulk operations don't
        trigger Django signals.

        Args:
            queryset: QuerySet of CourseSessionModel objects to update
            **update_fields: Fields to update

        Returns:
            int: Number of updated sessions
        """
        # Get the IDs before bulk update
        session_ids = list(queryset.values_list("id", flat=True))

        # Perform bulk update
        updated_count = queryset.update(**update_fields)

        if updated_count > 0:
            # Manually sync each updated session
            updated_sessions = cls.objects.filter(id__in=session_ids)

            for session in updated_sessions:
                # Import here to avoid circular imports
                from lab_schedule.models import LabScheduleModel

                try:
                    LabScheduleModel.sync_from_course_session(session)
                except Exception as e:
                    # Log error but don't stop the process
                    import logging

                    logger = logging.getLogger("application.course")
                    logger.error(
                        f"Failed to sync session {session.id} to lab schedule: {e}"
                    )

        return updated_count

    @classmethod
    def bulk_deactivate_with_sync(cls, **filters):
        """
        Bulk deactivate course sessions with lab schedule sync.

        Args:
            **filters: Filters for the queryset

        Returns:
            int: Number of deactivated sessions
        """
        queryset = cls.objects.filter(is_active=True, **filters)
        return cls.bulk_update_with_sync(queryset, is_active=False)

    @classmethod
    def bulk_activate_with_sync(cls, **filters):
        """
        Bulk activate course sessions with lab schedule sync.

        Args:
            **filters: Filters for the queryset

        Returns:
            int: Number of activated sessions
        """
        queryset = cls.objects.filter(is_active=False, **filters)
        return cls.bulk_update_with_sync(queryset, is_active=True)
