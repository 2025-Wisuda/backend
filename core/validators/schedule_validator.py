"""
Schedule Validator for Django Models

Provides comprehensive scheduling validation functionality for models with date/time fields.
This validator handles all scheduling-related validation logic including operating hours,
conflict detection, and time validation.

Features:
- Date and time field validation
- Operating hours enforcement
- Schedule conflict detection
- Past date validation
- Current time validation for same-day schedules
- Configurable field names to work with different models
- Customizable conflict filtering

Usage:
    from core.validators import ScheduleValidator
    
    class MyScheduleModel(BaseModel):
        schedule_date = models.DateField()
        start_time = models.TimeField()
        end_time = models.TimeField()
        
        def clean(self):
            super().clean()
            validator = ScheduleValidator(
                instance=self,
                model_class=MyScheduleModel
            )
            validator.validate()
    
    # Custom field names example:
    class CustomScheduleModel(BaseModel):
        booking_date = models.DateField()
        begin_time = models.TimeField()
        finish_time = models.TimeField()
        
        def clean(self):
            super().clean()
            validator = ScheduleValidator(
                instance=self,
                model_class=CustomScheduleModel,
                date_field="booking_date",
                start_time_field="begin_time",
                end_time_field="finish_time"
            )
            validator.validate()
    
    # With custom conflict filtering:
    class RoomBooking(BaseModel):
        room = models.ForeignKey(Room, on_delete=models.CASCADE)
        schedule_date = models.DateField()
        start_time = models.TimeField()
        end_time = models.TimeField()
        
        def clean(self):
            super().clean()
            def room_conflict_filter(queryset):
                return queryset.filter(room=self.room)
                
            validator = ScheduleValidator(
                instance=self,
                model_class=RoomBooking,
                conflict_filter=room_conflict_filter
            )
            validator.validate()
"""

from datetime import date

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from shared.constant import LabOperatingHoursConstant


class ScheduleValidator:
    """
    Validator for schedule-related functionality.

    Handles validation of scheduling models including date/time validation,
    operating hours enforcement, conflict detection, and time-based business rules.
    """

    def __init__(
        self,
        instance,
        model_class,
        date_field="schedule_date",
        start_time_field="start_time",
        end_time_field="end_time",
        pk_field="pk",
        conflict_filter=None,
        cross_model_classes=None,
    ):
        """
        Args:
            instance: model instance to validate
            model_class: model class for querying conflicts (primary model)
            date_field: name of the date field on the model (default 'schedule_date')
            start_time_field: name of the start time field (default 'start_time')
            end_time_field: name of the end time field (default 'end_time')
            pk_field: name of primary key field (default 'pk')
            conflict_filter: optional Q object or callable returning QuerySet to filter conflicts
            cross_model_classes: list of additional model classes to check for conflicts
        """
        self.instance = instance
        self.model_class = model_class
        self.date_field = date_field
        self.start_time_field = start_time_field
        self.end_time_field = end_time_field
        self.pk_field = pk_field
        self.conflict_filter = conflict_filter
        self.cross_model_classes = cross_model_classes or []

    def validate(self):
        """Run all scheduling validations."""
        self.validate_dates()
        self.validate_times()
        self.validate_operating_hours()
        self.validate_start_date_not_past()
        self.validate_conflicts()

    def validate_dates(self):
        """Validate that date fields contain valid date values."""
        date_val = getattr(self.instance, self.date_field, None)
        if date_val and not isinstance(date_val, date):
            raise ValidationError({self.date_field: _("Invalid date value.")})

    def validate_start_date_not_past(self):
        """Validate that schedule date is not in the past."""
        date_val = getattr(self.instance, self.date_field, None)
        if date_val and date_val < timezone.localdate():
            raise ValidationError({self.date_field: _("Date cannot be in the past.")})

    def validate_times(self):
        """
        Validate time fields and business rules.

        Ensures:
        - Start time is before end time
        - For same-day schedules, start time is not in the past
        """
        st = getattr(self.instance, self.start_time_field, None)
        et = getattr(self.instance, self.end_time_field, None)
        date_val = getattr(self.instance, self.date_field, None)

        if st and et:
            if st >= et:
                raise ValidationError(
                    {self.end_time_field: _("End time must be after start time.")}
                )

            if date_val == timezone.localdate():
                now_time = timezone.localtime().time()
                if st < now_time:
                    raise ValidationError(
                        {
                            self.start_time_field: _(
                                "Start time cannot be earlier than current time."
                            )
                        }
                    )

    def validate_operating_hours(self):
        """Validate that times are within lab operating hours."""
        st = getattr(self.instance, self.start_time_field, None)
        et = getattr(self.instance, self.end_time_field, None)

        if st:
            if st < LabOperatingHoursConstant.START_TIME:
                raise ValidationError(
                    {
                        self.start_time_field: _(
                            "Start time must be after lab opening time (%(start_time)s)."
                        )
                        % {
                            "start_time": LabOperatingHoursConstant.START_TIME.strftime(
                                "%H:%M"
                            )
                        }
                    }
                )
            if st > LabOperatingHoursConstant.END_TIME:
                raise ValidationError(
                    {
                        self.start_time_field: _(
                            "Start time must be before lab closing time (%(end_time)s)."
                        )
                        % {
                            "end_time": LabOperatingHoursConstant.END_TIME.strftime(
                                "%H:%M"
                            )
                        }
                    }
                )

        if et:
            if et > LabOperatingHoursConstant.END_TIME:
                raise ValidationError(
                    {
                        self.end_time_field: _(
                            "End time must be before lab closing time (%(end_time)s)."
                        )
                        % {
                            "end_time": LabOperatingHoursConstant.END_TIME.strftime(
                                "%H:%M"
                            )
                        }
                    }
                )
            if et < LabOperatingHoursConstant.START_TIME:
                raise ValidationError(
                    {
                        self.end_time_field: _(
                            "End time must be after lab opening time (%(start_time)s)."
                        )
                        % {
                            "start_time": LabOperatingHoursConstant.START_TIME.strftime(
                                "%H:%M"
                            )
                        }
                    }
                )

    def validate_conflicts(self):
        """
        Validate that the schedule does not conflict with existing entries.

        Checks for time overlaps on the same date, excluding the current instance
        if it's an update operation. Also checks across multiple model classes
        if cross_model_classes is provided for cross-model conflict detection.
        """
        date_val = getattr(self.instance, self.date_field, None)
        st = getattr(self.instance, self.start_time_field, None)
        et = getattr(self.instance, self.end_time_field, None)

        if not (date_val and st and et):
            return

        # Check conflicts in primary model class
        conflicts_found = self._check_model_conflicts(
            self.model_class,
            date_val,
            st,
            et,
            exclude_pk=getattr(self.instance, self.pk_field, None),
        )

        if conflicts_found:
            raise ValidationError(_("Schedule conflicts with existing entries."))

        # Check conflicts in cross-model classes (for cross-model validation)
        for model_class in self.cross_model_classes:
            cross_conflicts = self._check_cross_model_conflicts(
                model_class, date_val, st, et
            )
            if cross_conflicts:
                raise ValidationError(
                    _("Schedule conflicts with existing entries in {}.").format(
                        model_class._meta.verbose_name
                    )
                )

    def _check_model_conflicts(
        self, model_class, date_val, start_time, end_time, exclude_pk=None
    ):
        """Check conflicts within a specific model class."""
        # Get the field mappings for this model class
        date_field = getattr(model_class, "SCHEDULE_DATE_FIELD", "schedule_date")
        start_field = getattr(model_class, "START_TIME_FIELD", "start_time")
        end_field = getattr(model_class, "END_TIME_FIELD", "end_time")

        qs = model_class.objects.filter(**{date_field: date_val})

        if callable(self.conflict_filter) and model_class == self.model_class:
            qs = self.conflict_filter(qs)

        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)

        qs = qs.filter(
            **{
                f"{start_field}__lt": end_time,
                f"{end_field}__gt": start_time,
            }
        )

        return qs.exists()

    def _check_cross_model_conflicts(self, model_class, date_val, start_time, end_time):
        """Check conflicts in cross-model classes."""
        return self._check_model_conflicts(model_class, date_val, start_time, end_time)
