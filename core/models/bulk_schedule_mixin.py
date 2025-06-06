"""
Bulk Schedule Mixin for Django Models

Provides bulk generation capability for models that need recurring schedule creation.
This mixin extends basic scheduling with bulk generation features.

Features:
- Bulk end date and days selection using BulkDays enum
- Accessor methods for bulk fields
- Validation and parsing utilities
- Reusable for lab schedule, duty schedule, etc.

Usage:
    from core.models import BaseModel, ApprovalMixin, ScheduleMixin, BulkScheduleMixin
    from core.enums import BulkDays
    
    class LabSchedule(BaseModel, ApprovalMixin, ScheduleMixin, BulkScheduleMixin):
        # Override field mapping to point to your custom field names
        SCHEDULE_DATE_FIELD = 'scheduled_date'
        START_TIME_FIELD = 'activity_start_time'
        END_TIME_FIELD = 'activity_end_time'
        BULK_END_DATE_FIELD = 'bulk_end_date'
        BULK_DAYS_FIELD = 'bulk_days'
        
        # Define your custom fields including bulk fields
        scheduled_date = models.DateField(...)
        activity_start_time = models.TimeField(...)
        activity_end_time = models.TimeField(...)
        bulk_end_date = models.DateField(null=True, blank=True, ...)
        bulk_days = models.CharField(choices=BulkDays.choices(), ...)

Required Fields (must be defined in your model):
- A bulk end date field mapped via BULK_END_DATE_FIELD
- A bulk days field mapped via BULK_DAYS_FIELD with BulkDays choices

Field Mapping Customization:
Override these class attributes to map to your field names:
- BULK_END_DATE_FIELD: defaults to 'bulk_end_date'
- BULK_DAYS_FIELD: defaults to 'bulk_days'
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ..enums.bulk_days_enum import BulkDays


class BulkScheduleMixin(models.Model):
    """
    Mixin that provides bulk schedule generation methods.
    Does not define fields - models must define their own bulk fields.

    Used for models that need to create multiple recurring schedules.
    """

    # Class attributes for field name customization - can be overridden
    BULK_END_DATE_FIELD = "bulk_end_date"
    BULK_DAYS_FIELD = "bulk_days"

    class Meta:
        abstract = True

    # Bulk generation accessor methods
    def get_bulk_end_date(self):
        """Get the bulk end date using mapped field name."""
        return getattr(self, self.BULK_END_DATE_FIELD, None)

    def set_bulk_end_date(self, value):
        """Set the bulk end date using mapped field name."""
        setattr(self, self.BULK_END_DATE_FIELD, value)

    def get_bulk_days(self):
        """Get the bulk days using mapped field name."""
        return getattr(self, self.BULK_DAYS_FIELD, None)

    def set_bulk_days(self, value):
        """Set the bulk days using mapped field name."""
        setattr(self, self.BULK_DAYS_FIELD, value)

    def is_bulk_generation(self):
        """Check if this is a bulk generation request."""
        bulk_end_date = self.get_bulk_end_date()
        bulk_days = self.get_bulk_days()
        return bulk_end_date is not None and bulk_days

    def get_bulk_days_list(self):
        """Parse bulk_days string into list of day names (Senin, Selasa, etc)."""
        bulk_days = self.get_bulk_days()
        if not bulk_days:
            return []
        try:
            # Split by comma and strip whitespace
            return [day.strip() for day in bulk_days.split(",") if day.strip()]
        except AttributeError:
            return []

    def get_bulk_weekdays_list(self):
        """Convert bulk_days into weekday numbers for date filtering (0=Monday, 6=Sunday)."""
        day_names = self.get_bulk_days_list()
        if not day_names:
            return []

        weekdays = []
        for day_name in day_names:
            try:
                weekdays.append(BulkDays[day_name.upper()].value)
            except KeyError:
                pass  # Ignore invalid day names

        return weekdays

    def set_bulk_days_from_list(self, days_list):
        """Set bulk_days from list of day names."""
        if not days_list:
            self.set_bulk_days(None)
        else:
            days_str = ",".join(days_list)
            self.set_bulk_days(days_str)

    def clear_bulk_fields(self):
        """Clear bulk generation fields after use."""
        self.set_bulk_end_date(None)
        self.set_bulk_days(None)

    def validate_bulk_fields(self):
        """Validate bulk generation fields."""
        if not self.is_bulk_generation():
            return True

        bulk_end_date = self.get_bulk_end_date()
        bulk_days_list = self.get_bulk_days_list()

        # Check if we have ScheduleMixin to get schedule_date
        if hasattr(self, "get_schedule_date"):
            schedule_date = self.get_schedule_date()
            if schedule_date and bulk_end_date and bulk_end_date < schedule_date:
                raise ValueError(
                    _("Bulk end date must be after or equal to schedule start date")
                )

        # Validate day names are valid Indonesian day names
        if bulk_days_list:
            valid_days = [
                "Senin",
                "Selasa",
                "Rabu",
                "Kamis",
                "Jumat",
                "Sabtu",
                "Minggu",
            ]
            invalid_days = [day for day in bulk_days_list if day not in valid_days]
            if invalid_days:
                raise ValueError(
                    _(
                        "Invalid day names: %(invalid_days)s. Must be one of: %(valid_days)s"
                    )
                    % {
                        "invalid_days": invalid_days,
                        "valid_days": ", ".join(valid_days),
                    }
                )

        return True
