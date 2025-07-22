"""
Lab Schedule Export Form for Django admin.

Provides filtering options for exporting lab schedule data with:
- Date filtering (date range, month, year)
- Activity type filtering
- Source model filtering  
- Field selection with checkboxes
- Centralized field definitions from LabScheduleResource (Single Source of Truth)

Architecture:
- FIELD_CHOICES: Auto-generated from LabScheduleResource.EXPORT_FIELDS
- No field duplication between resource and form
- Consistent field availability across import/export operations
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from core.enums import Month
from shared.export import BaseExportForm, ModelSpecificExportFormMixin

from ...models import LabScheduleModel
from ..lab_schedule_resource import LabScheduleResource


class LabScheduleExportForm(BaseExportForm, ModelSpecificExportFormMixin):
    """
    Lab Schedule-specific export form with filtering and field selection.

    Features:
    - Date filtering (range, month, year)
    - Activity type and source model filtering
    - Field selection with checkboxes
    - Centralized field definitions (No Duplication!)
    - Only exports active schedules (soft delete protection)

    Field Management:
    - FIELD_CHOICES: Auto-generated from LabScheduleResource.EXPORT_FIELDS
    - DEFAULT_FIELDS: Commonly used fields pre-selected
    - Only active schedules exported (is_active filter automatic)
    """

    # Field selection - Centralized from LabScheduleResource (Single Source of Truth)
    FIELD_CHOICES = [
        (field, _(field.replace("_", " ").title()))
        for field in LabScheduleResource.EXPORT_FIELDS
    ]

    # Default selected fields for user convenience
    DEFAULT_FIELDS = [
        "date",
        "start_time",
        "end_time",
        "type",
        "detail",
        "source_model",
    ]

    def _setup_custom_fields(self):
        """Setup lab schedule specific fields."""
        # Add schedule date range filtering
        self.fields["date_from"] = forms.DateField(
            required=False,
            widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            label=_("Schedule Date From"),
            help_text=_("Filter schedules from this date"),
        )

        self.fields["date_to"] = forms.DateField(
            required=False,
            widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            label=_("Schedule Date To"),
            help_text=_("Filter schedules until this date"),
        )

        # Add schedule month/year filtering using Month enum
        self.add_choice_filter(
            "schedule_month", Month.choices(include_all=True), _("Schedule Month")
        )

        self.fields["schedule_year"] = forms.IntegerField(
            required=False,
            widget=forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "2020",
                    "max": "2030",
                    "placeholder": _("Year"),
                }
            ),
            label=_("Schedule Year"),
            help_text=_("Filter by specific year"),
        )

        # Add source model filtering - only the 3 source models that create lab schedules
        SOURCE_MODEL_CHOICES = [
            ("LabAllocation", _("Lab Allocation")),
            ("CourseSession", _("Course Session")),
            ("RoomBooking", _("Room Booking")),
        ]
        self.add_choice_filter("source_model", SOURCE_MODEL_CHOICES, _("Source Model"))

    def _clean_custom(self, cleaned_data):
        """Custom validation for lab schedule export form."""
        # Validate schedule date range
        schedule_from = cleaned_data.get("date_from")
        schedule_to = cleaned_data.get("date_to")

        if schedule_from and schedule_to and schedule_from > schedule_to:
            raise forms.ValidationError(
                {"date_to": _("Schedule end date must be after start date")}
            )

        # Validate source model choice if provided
        source_model = cleaned_data.get("source_model")
        if source_model:
            valid_choices = ["LabAllocation", "CourseSession", "RoomBooking"]
            if source_model not in valid_choices:
                raise forms.ValidationError(
                    {"source_model": _("Invalid source model choice.")}
                )
        return cleaned_data

    def _get_custom_filter_summary(self, data):
        """
        Get summary of applied custom filters for display.

        Returns user-friendly filter descriptions for UI display.
        """
        summary = []

        # Schedule date range filters
        schedule_from = data.get("date_from")
        schedule_to = data.get("date_to")
        if schedule_from and schedule_to:
            summary.append(f"Schedule Date: {schedule_from} to {schedule_to}")
        elif schedule_from:
            summary.append(f"Schedule Date: from {schedule_from}")
        elif schedule_to:
            summary.append(f"Schedule Date: until {schedule_to}")

        # Schedule month filter
        schedule_month = data.get("schedule_month")
        if schedule_month:
            month_name = Month.get_month_name(int(schedule_month))
            if month_name:
                summary.append(f"Schedule Month: {month_name}")

        # Schedule year filter
        schedule_year = data.get("schedule_year")
        if schedule_year:
            summary.append(f"Schedule Year: {schedule_year}")

        # Source model filter
        source_model_filter = data.get("source_model")
        if source_model_filter:
            source_names = {
                "LabAllocation": "Lab Allocation",
                "CourseSession": "Course Session",
                "RoomBooking": "Room Booking",
            }
            summary.append(
                f"Source: {source_names.get(source_model_filter, source_model_filter)}"
            )

        return summary
