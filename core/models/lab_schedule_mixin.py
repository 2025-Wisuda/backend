"""
Schedule Mixin for Django Models

Provides reusable scheduling interface for models that need time-based scheduling.
This mixin is independent and provides accessor methods and validation.
Models must define their own schedule fields with custom names.

Features:
- Accessor methods for schedule fields
- Customizable field name mapping via class attributes
- Complete validation using ScheduleValidator (dates, times, operating hours, conflicts)
- Compatible with ApprovalMixin for approval workflow

Usage:
    from core.models import BaseModel, ApprovalMixin, LabSchedueMixin
    
    class LabScheduleModel(BaseModel, ApprovalMixin, LabSchedueMixin):
        # Override field mapping to point to your custom field names
        SCHEDULE_DATE_FIELD = 'scheduled_date'
        START_TIME_FIELD = 'activity_start_time'
        END_TIME_FIELD = 'activity_end_time'
        
        # Define your custom fields
        scheduled_date = models.DateField(
            db_index=True,
            verbose_name=_("Scheduled Date"),
        )
        activity_start_time = models.TimeField(
            verbose_name=_("Activity Start Time"),
        )
        activity_end_time = models.TimeField(
            null=True, blank=True,
            verbose_name=_("Activity End Time"),
        )

Required Fields (must be defined in your model):
- A date field mapped via SCHEDULE_DATE_FIELD
- A start time field mapped via START_TIME_FIELD
- An end time field mapped via END_TIME_FIELD (optional)

Field Mapping Customization:
Override these class attributes to map to your field names:
- SCHEDULE_DATE_FIELD: defaults to 'schedule_date'
- START_TIME_FIELD: defaults to 'start_time'
- END_TIME_FIELD: defaults to 'end_time'
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class LabScheduleMixin(models.Model):
    """
    Interface mixin that provides scheduling methods and validation.
    Does not define fields - models must define their own schedule fields.
    """

    # Class attributes for field name customization - can be overridden
    SCHEDULE_DATE_FIELD = "schedule_date"
    START_TIME_FIELD = "start_time"
    END_TIME_FIELD = "end_time"

    class Meta:
        abstract = True

    def clean(self):
        """Run complete schedule validation using ScheduleValidator."""
        super().clean()

        from ..validators import ScheduleValidator

        # Set up cross-model conflict detection
        cross_model_classes = []

        # For cross-model conflict detection, include LabScheduleModel aggregator if available
        # and if this instance is not already a LabScheduleModel
        try:
            from lab_schedule.models import LabScheduleModel

            if not isinstance(self, LabScheduleModel):
                cross_model_classes.append(LabScheduleModel)
        except ImportError:
            pass

        validator = ScheduleValidator(
            instance=self,
            model_class=self.__class__,
            date_field=self.SCHEDULE_DATE_FIELD,
            start_time_field=self.START_TIME_FIELD,
            end_time_field=self.END_TIME_FIELD,
            cross_model_classes=cross_model_classes,
        )
        validator.validate()

    # Accessor methods using field mapping
    def get_schedule_date(self):
        """Get the schedule date using mapped field name."""
        return getattr(self, self.SCHEDULE_DATE_FIELD)

    def set_schedule_date(self, value):
        """Set the schedule date using mapped field name."""
        setattr(self, self.SCHEDULE_DATE_FIELD, value)

    def get_start_time(self):
        """Get the start time using mapped field name."""
        return getattr(self, self.START_TIME_FIELD)

    def set_start_time(self, value):
        """Set the start time using mapped field name."""
        setattr(self, self.START_TIME_FIELD, value)

    def get_end_time(self):
        """Get the end time using mapped field name."""
        return getattr(self, self.END_TIME_FIELD)

    def set_end_time(self, value):
        """Set the end time using mapped field name."""
        setattr(self, self.END_TIME_FIELD, value)
