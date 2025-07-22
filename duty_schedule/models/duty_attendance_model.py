"""
DutyAttendanceModel - Simplified for OTP + Face Recognition + Manual Override

Flow:
1. OTP validation
2. Face recognition attendance
3. Manual override (fallback)
"""

from datetime import datetime

from core import AttendanceStatus, BaseModel, UserGroup
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class DutyAttendanceModel(BaseModel):
    """
    Simplified duty attendance model.

    Flow:
    1. Mobile: POST OTP validation
    2. Mobile: Face recognition or manual override
    3. Backend: Mark attendance
    """

    duty_schedule = models.ForeignKey(
        "DutyScheduleModel",
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name=_("Duty Schedule"),
    )

    laboratory_assistant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"groups__name": UserGroup.LABORATORY_ASSISTANT.value},
        related_name="duty_attendances",
        verbose_name=_("Laboratory Assistant"),
    )

    date = models.DateField(
        db_index=True,
        verbose_name=_("Duty Date"),
    )

    start_time = models.TimeField(
        verbose_name=_("Start Time"),
    )

    end_time = models.TimeField(
        verbose_name=_("End Time"),
    )

    clock_in_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Clock In Time"),
    )

    clock_out_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Clock Out Time"),
    )

    otp_validated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("OTP Validated At"),
    )

    face_recognition_confidence = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Recognition Confidence"),
        help_text=_("Confidence score from face recognition (0.0-1.0)"),
    )

    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices(),
        default=AttendanceStatus.SCHEDULED.value,
        db_index=True,
        verbose_name=_("Status"),
    )

    # Manual override
    manual_clock_in_override = models.BooleanField(
        default=False,
        verbose_name=_("Manual Clock In Override"),
    )

    manual_clock_out_override = models.BooleanField(
        default=False,
        verbose_name=_("Manual Clock Out Override"),
    )

    # Additional fields
    face_recognition_person_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Face Recognition Person ID"),
    )

    face_recognition_request_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Face Recognition Request ID"),
    )

    otp_used_for_attendance = models.BooleanField(
        default=False,
        verbose_name=_("OTP Used for Attendance"),
    )

    class Meta:
        db_table = "duty_attendance"
        ordering = ["date", "start_time", "laboratory_assistant"]
        verbose_name = _("Duty Attendance")
        verbose_name_plural = _("Duty Attendances")
        unique_together = [["duty_schedule", "laboratory_assistant", "date"]]
        indexes = [
            models.Index(fields=["date", "status"]),
            models.Index(fields=["laboratory_assistant", "date"]),
            models.Index(fields=["clock_in_time"]),
            models.Index(fields=["otp_validated_at"]),
        ]

    def __str__(self):
        return f"{self.laboratory_assistant} - {self.date} ({self.status})"

    def save(self, *args, **kwargs):
        """Always auto-calculate status based on clock times."""
        self.status = self._calculate_auto_status()
        super().save(*args, **kwargs)

    def _calculate_auto_status(self):
        """Auto-calculate status based on clock in/out."""
        duty_end_datetime = datetime.combine(self.date, self.end_time)
        duty_end_datetime = timezone.make_aware(duty_end_datetime)
        current_time = timezone.localtime()

        if not self.clock_in_time:
            if current_time > duty_end_datetime:
                return AttendanceStatus.ABSENT.value
            return AttendanceStatus.SCHEDULED.value

        if not self.clock_out_time:
            if current_time > duty_end_datetime:
                return AttendanceStatus.EARLY_OUT.value

        local_clock_in_time = timezone.localtime(self.clock_in_time)

        if local_clock_in_time.date() != self.date:
            return AttendanceStatus.ABSENT.value

        if local_clock_in_time.time() > self.start_time:
            return AttendanceStatus.LATE.value
        else:
            return AttendanceStatus.PRESENT.value

    def mark_otp_validated(self):
        """Mark OTP as validated."""
        self.otp_validated_at = timezone.localtime()
        self.save(update_fields=["otp_validated_at"])

    def manual_clock_in(self, status="Hadir", user=None):
        """Manual clock in - just set time, status auto-calculated."""
        self.clock_in_time = timezone.localtime()
        self.manual_clock_in_override = True
        self.face_recognition_confidence = None
        self.face_recognition_person_id = None
        self.face_recognition_request_id = None
        if user:
            self.updated_by = user
        self.save()

    def manual_clock_out(self, status="Hadir", user=None):
        """
        Manual clock out dengan status.

        Args:
            status (str): Attendance status (Hadir, Terlambat, etc.)
            user (User): User who performed manual clock out
        """
        if not self.clock_in_time:
            self.clock_in_time = timezone.localtime()

        self.clock_out_time = timezone.localtime()
        self.status = status
        self.manual_clock_out_override = True
        self.face_recognition_confidence = None
        self.face_recognition_person_id = None
        self.face_recognition_request_id = None

        if user:
            self.updated_by = user
        self.save()

    def clock_in_via_face_recognition(self, person_id, confidence, request_id=None):
        """
        Clock in via face recognition after OTP validation.

        Args:
            person_id (str): Person ID from face recognition
            confidence (float): Confidence score (0.0-1.0)
            request_id (str): WebSocket request ID
        """
        self.clock_in_time = timezone.localtime()
        self.face_recognition_person_id = person_id
        self.face_recognition_confidence = confidence
        self.face_recognition_request_id = request_id
        self.otp_used_for_attendance = True
        self.save()

    def clock_out_via_face_recognition(self, person_id, confidence, request_id=None):
        """
        Clock out via face recognition.

        Args:
            person_id (str): Person ID from face recognition
            confidence (float): Confidence score (0.0-1.0)
            request_id (str): WebSocket request ID
        """
        self.clock_out_time = timezone.localtime()
        # Update face recognition data (for latest recognition)
        self.face_recognition_person_id = person_id
        self.face_recognition_confidence = confidence
        self.face_recognition_request_id = request_id
        self.save()

    def is_otp_validated(self):
        """Check if OTP was validated recently (within 5 minutes)."""
        if not self.otp_validated_at:
            return False

        time_diff = timezone.localtime() - self.otp_validated_at
        return time_diff.total_seconds() <= 300  # 5 minutes

    def is_present(self):
        """Check if assistant was present."""
        return self.status in [
            AttendanceStatus.PRESENT.value,
            AttendanceStatus.LATE.value,
        ]

    def get_confidence_percentage(self):
        """Get confidence as percentage."""
        if self.face_recognition_confidence:
            return round(self.face_recognition_confidence * 100, 1)
        return None

    def can_clock_in(self):
        """Check if can clock in (OTP validated and not already clocked in)."""
        return self.is_otp_validated() and not self.clock_in_time

    def can_clock_out(self):
        """Check if can clock out (already clocked in, not clocked out)."""
        return self.clock_in_time and not self.clock_out_time
