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

from core import BaseModel, BulkScheduleMixin, DaysEnum, UserGroup
from core.enums.bulk_days_enum import BulkDays
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
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
    - BULK_END_DATE_FIELD: 'end_date'
    - BULK_DAYS_FIELD: 'days'
    """

    # Field mapping for BulkScheduleMixin
    BULK_END_DATE_FIELD = "end_date"
    BULK_DAYS_FIELD = "days"

    # Assistant assignment (many-to-many for multiple assistants)
    laboratory_assistants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="bulk_duty_schedules",
        limit_choices_to={"groups__name": UserGroup.LABORATORY_ASSISTANT.value},
        verbose_name=_("Assigned Teaching Assistants"),
        help_text=_("Select teaching assistants for this duty schedule"),
    )

    # Date range for bulk generation
    start_date = models.DateField(
        verbose_name=_("Duty Start Date"),
        help_text=_("Start date for the duty period"),
    )

    end_date = models.DateField(
        verbose_name=_("Duty End Date"),
        help_text=_("End date for bulk generation"),
    )

    # Time range with defaults from lab hours
    start_time = models.TimeField(
        default=LabOperatingHoursConstant.START_TIME,
        verbose_name=_("Duty Start Time"),
        help_text=_("Start time for duty shifts"),
    )

    end_time = models.TimeField(
        default=LabOperatingHoursConstant.END_TIME,
        verbose_name=_("Duty End Time"),
        help_text=_("End time for duty shifts"),
    )

    # Days pattern for bulk generation
    days = models.CharField(
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
        ordering = ["start_date", "start_time"]
        verbose_name = _("Duty Schedule (Bulk)")
        verbose_name_plural = _("Duty Schedules (Bulk)")

        # Index for efficient querying
        indexes = [
            models.Index(fields=["start_date", "end_date"]),
            models.Index(fields=["is_generated"]),
        ]

    def __str__(self):
        """String representation of the duty schedule."""
        assistants_count = self.laboratory_assistants.count()
        return f"{self.days} ({self.start_date} - {assistants_count} assistants)"

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
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError(
                {"end_date": _("End date must be after or equal to start date.")}
            )

    def _validate_times(self):
        """Validate time fields."""
        if self.end_time <= self.start_time:
            raise ValidationError({"end_time": _("End time must be after start time.")})

        # Validate against lab operating hours
        if (
            self.start_time < LabOperatingHoursConstant.START_TIME
            or self.end_time > LabOperatingHoursConstant.END_TIME
        ):
            raise ValidationError(
                {
                    "start_time": _(
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
        if not self.days:
            return  # Skip conflict detection if no days pattern

        # Find overlapping schedules with same days pattern
        overlapping_schedules = DutyScheduleModel.objects.filter(
            is_active=True,
            days=self.days,
            start_date__lte=self.end_date or self.start_date,
            end_date__gte=self.start_date,
        )

        # Exclude current instance if updating
        if self.pk:
            overlapping_schedules = overlapping_schedules.exclude(pk=self.pk)

        # Check for time conflicts within the overlapping schedules
        for schedule in overlapping_schedules:
            if self._times_overlap(schedule):
                raise ValidationError(
                    {
                        "days": _(
                            f"Schedule conflict detected with '{schedule.days}' "
                            f"({schedule.start_date} - {schedule.end_date or schedule.start_date}). "
                            f"Same days pattern '{self.days}' with overlapping times."
                        )
                    }
                )

    def _times_overlap(self, other_schedule):
        """Check if time ranges overlap with another schedule."""
        return not (
            self.end_time <= other_schedule.start_time
            or self.start_time >= other_schedule.end_time
        )

    def generate_attendance_records(self, commit=True):
        """
        Generate individual DutyAttendanceModel records based on this schedule.
        
        Updated for OTP + Face Recognition model.

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
        assistants = list(self.laboratory_assistants.all())

        if not assistants:
            raise ValidationError(
                _(
                    "At least one assistant must be assigned before generating attendance records."
                )
            )

        attendance_records = []

        for date in dates:
            for assistant in assistants:
                # Create attendance record - Django will use model defaults for other fields
                attendance = DutyAttendanceModel(
                    duty_schedule=self,
                    laboratory_assistant=assistant,
                    date=date,
                    start_time=self.start_time,
                    end_time=self.end_time,
                )
                
                # Set BaseModel fields if available
                if hasattr(self, 'created_by') and self.created_by:
                    attendance.created_by = self.created_by
                if hasattr(self, 'updated_by') and self.updated_by:
                    attendance.updated_by = self.updated_by
                    
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
            return [self.start_date]

        # Get weekday numbers for the selected days using BulkDays enum
        weekdays = BulkDays.get_weekday_numbers(self.days)
        if not weekdays:
            return [self.start_date]

        dates = []
        current_date = self.start_date
        end_date = self.end_date or self.start_date

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
            .exclude(status=AttendanceStatus.SCHEDULED.value)
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

    def generate_missing_attendance_records(self, commit=True):
        """
        Generate only missing attendance records (incremental generation).
        
        This method will:
        1. Check existing attendance records
        2. Only create records that don't exist yet
        3. Skip existing records (including scheduled ones)
        
        This is safer for updates as it preserves existing attendance data.

        Args:
            commit (bool): Whether to save to database immediately

        Returns:
            tuple: (newly_created_records, existing_records_count)
        """
        from .duty_attendance_model import DutyAttendanceModel

        # Generate date list based on pattern
        dates = self._generate_date_list()
        assistants = list(self.laboratory_assistants.all())

        if not assistants:
            raise ValidationError(
                _(
                    "At least one assistant must be assigned before generating attendance records."
                )
            )

        new_attendance_records = []
        existing_count = 0

        for date in dates:
            for assistant in assistants:
                # Check if attendance record already exists
                existing_record = DutyAttendanceModel.objects.filter(
                    duty_schedule=self,
                    laboratory_assistant=assistant,
                    date=date,
                    is_active=True,
                ).first()

                if existing_record:
                    # Skip if record already exists
                    existing_count += 1
                    continue

                # Create new attendance record only if it doesn't exist
                attendance = DutyAttendanceModel(
                    duty_schedule=self,
                    laboratory_assistant=assistant,
                    date=date,
                    start_time=self.start_time,
                    end_time=self.end_time,
                )
                
                # Set BaseModel fields if available
                if hasattr(self, 'created_by') and self.created_by:
                    attendance.created_by = self.created_by
                if hasattr(self, 'updated_by') and self.updated_by:
                    attendance.updated_by = self.updated_by
                    
                new_attendance_records.append(attendance)

        if commit and new_attendance_records:
            # Bulk create only new records
            DutyAttendanceModel.objects.bulk_create(new_attendance_records)

        # Update generation status and count
        total_expected = len(dates) * len(assistants)
        total_existing = existing_count + len(new_attendance_records)
        
        if commit:
            self.is_generated = (total_existing >= total_expected)
            self.generated_count = total_existing
            self.save(update_fields=["is_generated", "generated_count"])

        return new_attendance_records, existing_count
