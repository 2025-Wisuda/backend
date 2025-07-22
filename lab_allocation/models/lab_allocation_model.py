from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core import (
    AllocationType,
    BaseModel,
    BulkDays,
    BulkScheduleMixin,
    LabScheduleMixin,
)


class LabAllocationModel(BaseModel, LabScheduleMixin, BulkScheduleMixin):
    """
    Model for technician lab allocation scheduling.

    This model stores information about lab allocations managed by technicians, including:
    - Type and description of the allocation (maintenance, preparation, etc.)
    - Date and time range with custom field names
    - Bulk generation capabilities for creating multiple allocations
    - Auto-approval workflow for technicians with conflict detection

    Custom allocation fields:
        - type: Type of the lab allocation (e.g. MAINTENANCE, PREPARATION)

    Schedule fields (overridden from LabScheduleMixin):
        - start_date: Date the allocation is scheduled
        - start_time: Starting time of the allocation
        - end_time: Ending time of the allocation

    Bulk generation fields (overridden from BulkScheduleMixin):
        - end_date: End date for bulk allocation generation
        - days: Days pattern using BulkDays enum

    Note: LabAllocationModel uses auto-approval for technicians+ roles.
    Only conflict detection is performed against other lab bookings.
    """

    SCHEDULE_DATE_FIELD = "start_date"
    START_TIME_FIELD = "start_time"
    END_TIME_FIELD = "end_time"

    BULK_END_DATE_FIELD = "end_date"
    BULK_DAYS_FIELD = "days"

    start_date = models.DateField(
        db_index=True,
        verbose_name=_("Allocation Date"),
        help_text=_("Date when the lab allocation is scheduled"),
    )
    start_time = models.TimeField(
        verbose_name=_("Allocation Start Time"),
        help_text=_("Start time of the lab allocation"),
    )
    end_time = models.TimeField(
        verbose_name=_("Allocation End Time"),
        help_text=_("End time of the lab allocation"),
    )

    type = models.CharField(
        max_length=20,
        db_index=True,
        choices=AllocationType.choices(),
        verbose_name=_("Allocation Type"),
        help_text=_("Type of laboratory allocation (maintenance, preparation, etc.)"),
        default=AllocationType.REGULAR_CLASS.value,
    )
    detail = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Allocation Details"),
        help_text=_("Detailed description of the lab allocation"),
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Allocation End Date"),
        help_text=_(
            "Leave empty for single allocation. Fill to create multiple allocations until this date."
        ),
    )
    days = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=BulkDays.choices(),
        verbose_name=_("Allocation Days"),
        help_text=_("Select days pattern for allocation generation"),
    )

    class Meta:
        db_table = "lab_allocation"
        ordering = ["start_date", "start_time"]
        verbose_name = _("Lab Allocation")
        verbose_name_plural = _("Lab Allocations")

    def __str__(self):
        return f"{self.created_by} - {self.type} ({self.start_date})"
