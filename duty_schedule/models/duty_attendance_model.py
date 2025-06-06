"""
DutyAttendanceModel for individual duty attendance tracking.

This model tracks individual attendance records with simplified manual clock in/out 
functionality, location validation, and OTP security for duty assignments.

Features:
- Individual attendance tracking per assistant per date
- Manual clock in/out with actual timestamps (default mode)
- Location validation for UNILA lab coordinates
- OTP validation for security
- Status tracking with automatic calculation
- Future support for face recognition (when needed)
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core import AttendanceStatus, BaseModel, UserGroup
from core.enums.clock_method_enum import ClockMethod
from core.validators import AttendanceLocationValidator, AttendanceStatusValidator


class DutyAttendanceModel(BaseModel):
    """
    Individual duty attendance model with simplified manual tracking.

    This model tracks individual attendance for each assistant on each duty date.
    Includes manual clock in/out functionality with location validation and security features.

    Features:
    - Cascade relationship to DutyScheduleModel
    - Individual assistant assignment
    - Duplicated time fields for performance (vs. always joining)
    - Manual clock in/out with actual timestamps (default mode)
    - Location tracking and validation for UNILA lab coordinates
    - Automatic status calculation based on times
    - Support for future face recognition integration
    """

    # Relationship to bulk schedule (cascade delete)
    duty_schedule = models.ForeignKey(
        "DutyScheduleModel",
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name=_("Source Duty Schedule"),
        help_text=_("The bulk schedule that generated this attendance record"),
    )

    # Assistant assignment (single assistant per record)
    duty_assistant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"groups__name": UserGroup.LABORATORY_ASSISTANT.value},
        related_name="duty_attendances",
        verbose_name=_("Teaching Assistant"),
        help_text=_("The assistant assigned to this duty"),
    )

    # Scheduled duty information (duplicated for performance)
    duty_date = models.DateField(
        db_index=True,
        verbose_name=_("Duty Date"),
        help_text=_("Date of the duty assignment"),
    )

    duty_start_time = models.TimeField(
        verbose_name=_("Scheduled Start Time"),
        help_text=_("Scheduled start time for the duty"),
    )

    duty_end_time = models.TimeField(
        verbose_name=_("Scheduled End Time"),
        help_text=_("Scheduled end time for the duty"),
    )

    # Actual attendance data
    clock_in_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Actual Clock In Time"),
        help_text=_("Actual time when assistant clocked in"),
    )

    clock_out_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Actual Clock Out Time"),
        help_text=_("Actual time when assistant clocked out"),
    )

    # Clock in/out methods using enum
    clock_in_method = models.CharField(
        max_length=20,
        choices=ClockMethod.choices(),
        default=ClockMethod.default(),
        verbose_name=_("Clock In Method"),
        help_text=_("Method used for clock in (manual or face_recognition)"),
    )

    clock_out_method = models.CharField(
        max_length=20,
        choices=ClockMethod.choices(),
        default=ClockMethod.default(),
        verbose_name=_("Clock Out Method"),
        help_text=_("Method used for clock out (manual or face_recognition)"),
    )

    # Location data (simplified JSON storage)
    clock_in_location = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Clock In Location"),
        help_text=_(
            "Location data for clock in including coordinates and verification"
        ),
    )

    clock_out_location = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Clock Out Location"),
        help_text=_(
            "Location data for clock out including coordinates and verification"
        ),
    )

    # Status tracking
    attendance_status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices(),
        default=AttendanceStatus.SCHEDULED.value,
        db_index=True,
        verbose_name=_("Attendance Status"),
        help_text=_("Current status of the attendance record"),
    )

    class Meta:
        db_table = "duty_attendance"
        ordering = ["duty_date", "duty_start_time", "duty_assistant"]
        verbose_name = _("Duty Attendance")
        verbose_name_plural = _("Duty Attendances")

        # Ensure unique attendance per assistant per date per schedule
        unique_together = [["duty_schedule", "duty_assistant", "duty_date"]]

        # Indexes for efficient querying
        indexes = [
            models.Index(fields=["duty_date", "attendance_status"]),
            models.Index(fields=["duty_assistant", "duty_date"]),
            models.Index(fields=["clock_in_time"]),
            models.Index(fields=["clock_out_time"]),
        ]

    def __str__(self):
        """String representation of the attendance record."""
        return f"{self.duty_assistant} - {self.duty_date} ({self.attendance_status})"

    def clean(self):
        """Validate attendance data using centralized validator."""
        super().clean()
        AttendanceStatusValidator.validate_time_sequence(
            self.clock_in_time, self.clock_out_time
        )

    def save(self, *args, **kwargs):
        """Override save to auto-calculate status."""
        self.attendance_status = self.calculate_status()
        super().save(*args, **kwargs)

    def calculate_status(self):
        """
        Calculate attendance status using centralized validator.

        Returns:
            str: Calculated attendance status
        """
        return AttendanceStatusValidator.calculate_attendance_status(
            self.duty_date,
            self.duty_start_time,
            self.duty_end_time,
            self.clock_in_time,
            self.clock_out_time,
        )

    def clock_in(self, method=None, location_data=None, user=None):
        """Clock in with validation."""
        AttendanceStatusValidator.validate_clock_in_preconditions(self.clock_in_time)

        if location_data:
            AttendanceLocationValidator.validate_unila_location(location_data)
            location_data["verified"] = True

        self.clock_in_time = timezone.now()
        self.clock_in_method = method or ClockMethod.default()
        self.clock_in_location = location_data

        if user:
            self.updated_by = user
        self.save()

    def clock_out(self, method=None, location_data=None, user=None):
        """Clock out with validation."""
        AttendanceStatusValidator.validate_clock_out_preconditions(
            self.clock_in_time, self.clock_out_time
        )

        if location_data:
            AttendanceLocationValidator.validate_unila_location(location_data)
            location_data["verified"] = True

        self.clock_out_time = timezone.now()
        self.clock_out_method = method or ClockMethod.default()
        self.clock_out_location = location_data

        if user:
            self.updated_by = user
        self.save()

    def manual_override(self, status, user):
        """Override attendance status manually."""
        AttendanceStatusValidator.validate_manual_override(status, user)

        if self.attendance_status:
            AttendanceStatusValidator.validate_status_transition(
                self.attendance_status, status
            )

        self.attendance_status = status
        self.updated_by = user
        self.save()

    def get_security_score(self):
        """Get security validation score."""
        return AttendanceStatusValidator.calculate_security_score(
            self.clock_in_time,
            self.clock_out_time,
            self.clock_in_location,
            self.clock_out_location,
            self.clock_in_method,
            self.clock_out_method,
        )

    def is_present(self):
        """Check if assistant was present."""
        return (
            self.attendance_status in AttendanceStatusValidator.get_present_statuses()
        )

    def is_completed(self):
        """Check if attendance is completed."""
        return (
            self.attendance_status in AttendanceStatusValidator.get_completed_statuses()
        )
