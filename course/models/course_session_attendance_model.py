from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from core import BaseModel
from core.enums import AttendanceStatus
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.db.models.manager import Manager


class CourseSessionAttendanceModel(BaseModel):
    if TYPE_CHECKING:
        objects: Manager[CourseSessionAttendanceModel]
    course_session = models.ForeignKey(
        "CourseSessionModel",
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name=_("Course Session"),
        help_text=_("The course session this attendance belongs to"),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_attendances",
        verbose_name=_("Student"),
        help_text=_("The student for this attendance record"),
    )

    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices(),
        default=AttendanceStatus.ABSENT,
        db_index=True,
        verbose_name=_("Attendance Status"),
        help_text=_("Current attendance status"),
    )

    marked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Marked At"),
        help_text=_("Timestamp when attendance was marked"),
    )

    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marked_attendances",
        verbose_name=_("Marked By"),
        help_text=_("Teaching assistant who marked the attendance"),
    )

    face_recognition_person_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Face Recognition Person ID"),
        help_text=_("Person ID returned from face recognition service"),
    )

    face_recognition_confidence = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Face Recognition Confidence"),
        help_text=_("Confidence score from face recognition (0.0-1.0)"),
    )

    face_recognition_request_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Face Recognition Request ID"),
        help_text=_("WebSocket request ID for face recognition"),
    )

    # Manual override (following duty attendance pattern)
    manual_attendance_override = models.BooleanField(
        default=False,
        verbose_name=_("Manual Attendance Override"),
        help_text=_("True if attendance was marked manually without face recognition"),
    )

    class Meta:
        db_table = "course_session_attendance"
        verbose_name = _("Course Session Attendance")
        verbose_name_plural = _("Course Session Attendances")
        unique_together = [["course_session", "student"]]

        indexes = [
            models.Index(fields=["course_session", "status"]),
            models.Index(fields=["student", "status"]),
            models.Index(fields=["marked_at"]),
            models.Index(fields=["face_recognition_person_id"]),
        ]

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course_session.title}"

    def clean(self):
        super().clean()
        errors = {}

        if self.marked_by and self.course_session:
            course = self.course_session.course
            if not course.teaching_assistants.filter(id=self.marked_by.id).exists():
                errors["marked_by"] = _(
                    "Only teaching assistants assigned to this course can mark attendance."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Always auto-calculate status based on timing, unless status is provided."""
        # Only auto-calculate if status is not explicitly set
        if "status" not in kwargs.get("update_fields", []):
            self.status = self._calculate_auto_status()

        # Skip clean() method if called from async context to avoid property access
        if kwargs.get("skip_clean", False):
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def _calculate_auto_status(self, session=None):
        """Auto-calculate status based on session timing."""
        # Get session safely - avoid property access that could trigger query
        if session is None:
            session = self.course_session

        # If no marked time, check if session has passed
        if not self.marked_at:
            session_end_datetime = datetime.combine(session.date, session.end_time)
            session_end_datetime = timezone.make_aware(session_end_datetime)
            current_time = timezone.localtime()

            # If session has ended and no mark, mark as absent
            if current_time > session_end_datetime:
                return AttendanceStatus.ABSENT.value

            return AttendanceStatus.ABSENT.value

        # Convert marked_at from UTC to local time for comparison
        local_marked_time = timezone.localtime(self.marked_at)

        # Check date
        if local_marked_time.date() != session.date:
            return AttendanceStatus.ABSENT.value

        # Check timing - tolerance based on session start time
        session_start_datetime = datetime.combine(session.date, session.start_time)
        session_start_datetime = timezone.make_aware(session_start_datetime)

        time_diff = (self.marked_at - session_start_datetime).total_seconds() / 60

        if time_diff <= 15:
            return AttendanceStatus.PRESENT.value
        elif time_diff <= 30:
            return AttendanceStatus.LATE.value
        else:
            return AttendanceStatus.ABSENT.value

    def manual_mark_attendance(self, user=None):
        """Manual attendance marking - just set time, status auto-calculated."""
        self.marked_at = timezone.localtime()
        self.manual_attendance_override = True
        self.face_recognition_confidence = None
        self.face_recognition_person_id = None
        self.face_recognition_request_id = None
        if user:
            self.marked_by = user
        self.save()

    def mark_attendance_via_face_recognition(
        self, person_id, confidence, marked_by_user, request_id=None
    ):
        """
        Mark attendance via face recognition.

        Args:
            person_id (str): Person ID from face recognition
            confidence (float): Confidence score (0.0-1.0)
            marked_by_user (User): TA who performed the face recognition attendance marking
            request_id (str): WebSocket request ID
        """
        self.marked_at = timezone.localtime()
        self.marked_by = marked_by_user
        self.face_recognition_person_id = person_id
        self.face_recognition_confidence = confidence
        self.face_recognition_request_id = request_id
        self.manual_attendance_override = False
        self.save()

    def is_present(self):
        """Check if student was present."""
        return self.status in [
            AttendanceStatus.PRESENT.value,
            AttendanceStatus.LATE.value,
        ]

    def get_confidence_percentage(self):
        """Get confidence as percentage."""
        if self.face_recognition_confidence:
            return round(self.face_recognition_confidence * 100, 1)
        return None

    def can_mark_attendance(self):
        """Check if attendance can be marked (not already marked)."""
        return self.marked_at is None

    @classmethod
    def bulk_generate_for_session(cls, course_session):
        """Generate attendance records for all enrolled students."""
        enrolled_students = course_session.course.students.filter(is_active=True)
        attendance_records = []
        existing_student_ids = set(
            cls.objects.filter(course_session=course_session).values_list(
                "student_id", flat=True
            )
        )

        for student in enrolled_students:
            if student.id not in existing_student_ids:
                attendance_records.append(
                    cls(
                        course_session=course_session,
                        student=student,
                        status=AttendanceStatus.ABSENT.value,
                        manual_attendance_override=False,
                    )
                )

        created_records = cls.objects.bulk_create(attendance_records)
        return len(created_records)
