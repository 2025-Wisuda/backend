"""
DutyScheduleModel for bulk generation of duty schedules.

This model handles bulk generation of duty schedules for laboratory assistants
using the BulkScheduleMixin pattern. It creates multiple DutyAttendanceModel
records based on date ranges and day patterns.

Features:
- Bulk generation of duty schedules for multiple assistants
- Date range and day pattern selection using BulkDays enum
- Conflict detection for overlapping schedules
- Integration with existing project validation patterns
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core import BaseModel, BulkScheduleMixin, DaysEnum, UserGroup
from core.enums.bulk_days_enum import BulkDays
from shared.constant import LabOperatingHoursConstant


class DutyScheduleModel(BaseModel, BulkScheduleMixin):
    """
    Model for bulk generation of duty schedules for laboratory assistants.

    This model creates templates for generating multiple individual duty
    attendance records (DutyAttendanceModel) based on date ranges and
    day patterns. Uses BulkScheduleMixin for bulk generation capabilities.

    Features:
    - Bulk generation with conflict detection
    - Assistant assignment with multiple assistants per schedule
    - Customizable time ranges with sensible defaults
    - Integration with existing validation patterns

    Field Mapping (for BulkScheduleMixin):
    - BULK_END_DATE_FIELD: 'duty_end_date'
    - BULK_DAYS_FIELD: 'duty_days'
    """

    # Field mapping for BulkScheduleMixin
    BULK_END_DATE_FIELD = "duty_end_date"
    BULK_DAYS_FIELD = "duty_days"

    # Assistant assignment (many-to-many for multiple assistants)
    duty_assistants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="bulk_duty_schedules",
        limit_choices_to={"groups__name": UserGroup.LABORATORY_ASSISTANT.value},
        verbose_name=_("Assigned Teaching Assistants"),
        help_text=_("Select teaching assistants for this duty schedule"),
    )

    # Date range for bulk generation
    duty_start_date = models.DateField(
        verbose_name=_("Duty Start Date"),
        help_text=_("Start date for the duty period"),
    )

    duty_end_date = models.DateField(
        verbose_name=_("Duty End Date"),
        help_text=_("End date for bulk generation"),
    )

    # Time range with defaults from lab hours
    duty_start_time = models.TimeField(
        default=LabOperatingHoursConstant.START_TIME,
        verbose_name=_("Duty Start Time"),
        help_text=_("Start time for duty shifts"),
    )

    duty_end_time = models.TimeField(
        default=LabOperatingHoursConstant.END_TIME,
        verbose_name=_("Duty End Time"),
        help_text=_("End time for duty shifts"),
    )

    # Days pattern for bulk generation
    duty_days = models.CharField(
        max_length=100,
        choices=BulkDays.choices(),
        verbose_name=_("Duty Days Pattern"),
        help_text=_(
            "Select days pattern for bulk generation (e.g., 'Senin,Rabu,Jumat')"
        ),
    )

    # Generation tracking
    is_generated = models.BooleanField(
        default=False,
        verbose_name=_("Is Generated"),
        help_text=_("Indicates whether attendance records have been generated"),
    )

    generated_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Generated Count"),
        help_text=_("Number of attendance records generated from this schedule"),
    )

    class Meta:
        db_table = "duty_schedule"
        ordering = ["duty_start_date", "duty_start_time"]
        verbose_name = _("Duty Schedule (Bulk)")
        verbose_name_plural = _("Duty Schedules (Bulk)")

        # Index for efficient querying
        indexes = [
            models.Index(fields=["duty_start_date", "duty_end_date"]),
            models.Index(fields=["is_generated"]),
        ]

    def __str__(self):
        """String representation of the duty schedule."""
        assistants_count = self.duty_assistants.count()
        return (
            f"{self.duty_days} ({self.duty_start_date} - {assistants_count} assistants)"
        )

    def clean(self):
        """
        Custom validation for duty schedule:
        1. Basic time and date validation
        2. Conflict detection for overlapping schedules with same days pattern
        """
        super().clean()

        # 1. Basic validation
        self._validate_dates()
        self._validate_times()

        # 2. Conflict detection for overlapping schedules
        if self.is_active:
            self._validate_schedule_conflicts()

    def _validate_dates(self):
        """Validate date fields."""
        if self.duty_end_date and self.duty_end_date < self.duty_start_date:
            raise ValidationError(
                {"duty_end_date": _("End date must be after or equal to start date.")}
            )

    def _validate_times(self):
        """Validate time fields."""
        if self.duty_end_time <= self.duty_start_time:
            raise ValidationError(
                {"duty_end_time": _("End time must be after start time.")}
            )

        # Validate against lab operating hours
        if (
            self.duty_start_time < LabOperatingHoursConstant.START_TIME
            or self.duty_end_time > LabOperatingHoursConstant.END_TIME
        ):
            raise ValidationError(
                {
                    "duty_start_time": _(
                        f"Duty time must be within lab operating hours "
                        f"({LabOperatingHoursConstant.START_TIME} - {LabOperatingHoursConstant.END_TIME})."
                    )
                }
            )

    def _validate_schedule_conflicts(self):
        """
        Check for conflicts with existing duty schedules that have:
        1. Overlapping date ranges
        2. Same days pattern
        3. Overlapping time ranges
        """
        if not self.duty_days:
            return  # Skip conflict detection if no days pattern

        # Find overlapping schedules with same days pattern
        overlapping_schedules = DutyScheduleModel.objects.filter(
            is_active=True,
            duty_days=self.duty_days,
            duty_start_date__lte=self.duty_end_date or self.duty_start_date,
            duty_end_date__gte=self.duty_start_date,
        )

        # Exclude current instance if updating
        if self.pk:
            overlapping_schedules = overlapping_schedules.exclude(pk=self.pk)

        # Check for time conflicts within the overlapping schedules
        for schedule in overlapping_schedules:
            if self._times_overlap(schedule):
                raise ValidationError(
                    {
                        "duty_days": _(
                            f"Schedule conflict detected with '{schedule.duty_days}' "
                            f"({schedule.duty_start_date} - {schedule.duty_end_date or schedule.duty_start_date}). "
                            f"Same days pattern '{self.duty_days}' with overlapping times."
                        )
                    }
                )

    def _times_overlap(self, other_schedule):
        """Check if time ranges overlap with another schedule."""
        return not (
            self.duty_end_time <= other_schedule.duty_start_time
            or self.duty_start_time >= other_schedule.duty_end_time
        )

    def generate_attendance_records(self, commit=True):
        """
        Generate individual DutyAttendanceModel records based on this schedule.

        Args:
            commit (bool): Whether to save to database immediately

        Returns:
            list: List of DutyAttendanceModel instances created
        """
        if self.is_generated:
            raise ValidationError(
                _("Attendance records have already been generated for this schedule.")
            )

        from .duty_attendance_model import DutyAttendanceModel

        # Generate date list based on pattern
        dates = self._generate_date_list()
        assistants = list(self.duty_assistants.all())

        if not assistants:
            raise ValidationError(
                _(
                    "At least one assistant must be assigned before generating attendance records."
                )
            )

        attendance_records = []

        for date in dates:
            for assistant in assistants:
                attendance = DutyAttendanceModel(
                    duty_schedule=self,
                    duty_assistant=assistant,
                    duty_date=date,
                    duty_start_time=self.duty_start_time,
                    duty_end_time=self.duty_end_time,
                    created_by=self.created_by,
                    updated_by=self.updated_by,
                )
                attendance_records.append(attendance)

        if commit:
            # Bulk create for efficiency
            DutyAttendanceModel.objects.bulk_create(attendance_records)

            # Update generation status
            self.is_generated = True
            self.generated_count = len(attendance_records)
            self.save(update_fields=["is_generated", "generated_count"])

        return attendance_records

    def _generate_date_list(self):
        """Generate list of dates based on start/end dates and days pattern."""
        from datetime import timedelta

        if not self.is_bulk_generation():
            return [self.duty_start_date]

        # Get weekday numbers for the selected days using BulkDays enum
        weekdays = BulkDays.get_weekday_numbers(self.duty_days)
        if not weekdays:
            return [self.duty_start_date]

        dates = []
        current_date = self.duty_start_date
        end_date = self.duty_end_date or self.duty_start_date

        while current_date <= end_date:
            # Check if current date's weekday matches our pattern
            # Python weekday: Monday=0, Sunday=6
            # BulkDays.get_weekday_numbers: Monday=0, Sunday=6 (same)
            if current_date.weekday() in weekdays:
                dates.append(current_date)
            current_date += timedelta(days=1)

        return dates

    def can_regenerate(self):
        """Check if attendance records can be regenerated."""
        if not self.is_generated:
            return True, _("No records generated yet.")

        # Check if any attendance has been marked (not just scheduled)
        from core.enums import AttendanceStatus

        from .duty_attendance_model import DutyAttendanceModel

        completed_attendance = (
            DutyAttendanceModel.objects.filter(duty_schedule=self, is_active=True)
            .exclude(attendance_status=AttendanceStatus.SCHEDULED.value)
            .exists()
        )

        if completed_attendance:
            return False, _(
                "Cannot regenerate: Some attendance records have been completed."
            )

        return True, _("Can regenerate (no completed attendance found).")

    def clear_attendance_records(self):
        """Clear generated attendance records (soft delete)."""
        from .duty_attendance_model import DutyAttendanceModel

        # Soft delete attendance records
        DutyAttendanceModel.objects.filter(duty_schedule=self, is_active=True).update(
            is_active=False
        )

        # Reset generation status
        self.is_generated = False
        self.generated_count = 0
        self.save(update_fields=["is_generated", "generated_count"])
