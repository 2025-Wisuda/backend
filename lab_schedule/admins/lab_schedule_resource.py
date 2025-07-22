"""
Lab schedule import/export resource for Django admin.

Export-only resource for laboratory schedule aggregator data.
No import functionality since this is a read-only aggregator.

Field Management (Single Source of Truth):
- EXPORT_FIELDS: Fields available for export (comprehensive)
- LabScheduleExportForm automatically uses EXPORT_FIELDS for field selection
- No duplication between resource and form definitions
"""

import locale

from django.utils.translation import gettext_lazy as _
from import_export import fields, resources

from shared.format.custom_xlsx_format import AutoFitXLSX

from ..models import LabScheduleModel

# Centralized field definitions - Single Source of Truth
# This eliminates duplication between resource and form definitions

EXPORT_FIELDS = (
    # Core schedule fields
    "date",
    "start_time",
    "end_time",
    "type",
    "detail",
    # Source tracking fields
    "source_model",
    "source_id",
    # Audit fields
    "created_at",
    "updated_at",
    "created_by",
    "updated_by",
)


class LabScheduleResource(resources.ModelResource):
    """
    Export-only resource for Lab Schedule aggregator data.

    Exports essential schedule information for reporting purposes.
    No import functionality since this is a read-only aggregator.

    Field Architecture:
    - EXPORT_FIELDS: Comprehensive set for export operations
    - Centralized definitions prevent duplication with forms
    - LabScheduleExportForm automatically inherits EXPORT_FIELDS choices
    """

    # Field constants for external access (used by LabScheduleExportForm)
    EXPORT_FIELDS = EXPORT_FIELDS

    type = fields.Field(
        column_name=_("Activity Type"),
        attribute="type",
    )

    date = fields.Field(
        column_name=_("Schedule Date"),
        attribute="date",
    )

    start_time = fields.Field(
        column_name=_("Start Time"),
        attribute="start_time",
    )

    end_time = fields.Field(
        column_name=_("End Time"),
        attribute="end_time",
    )

    detail = fields.Field(
        column_name=_("Activity Detail"),
        attribute="detail",
    )

    source_model = fields.Field(
        column_name=_("Source Model"),
        attribute="source_model",
    )

    source_id = fields.Field(
        column_name=_("Source ID"),
        attribute="source_id",
    )

    def get_export_headers(self, *args, **kwargs):
        """Convert field names to Title Case (e.g., date → Schedule Date)."""
        headers = super().get_export_headers(*args, **kwargs)
        return [header.replace("_", " ").title() for header in headers]

    def dehydrate_date(self, obj):
        """
        Format date as '4 Juni 2025'.
        Falls back to default locale if Indonesian locale not found.
        """
        date = obj.date
        try:
            locale.setlocale(locale.LC_TIME, "id_ID.utf8")
        except locale.Error:
            pass  # fallback: will format in English

        day = date.strftime("%d").lstrip("0")  # Remove leading zero
        month_year = date.strftime("%B %Y")
        return f"{day} {month_year}"

    def dehydrate_start_time(self, obj):
        """
        Format start_time as HH:MM (e.g., 17:00)
        """
        if obj.start_time:
            return obj.start_time.strftime("%H:%M")
        return ""

    def dehydrate_end_time(self, obj):
        """
        Format end_time as HH:MM (e.g., 18:30)
        """
        if obj.end_time:
            return obj.end_time.strftime("%H:%M")
        return ""

    def dehydrate_detail(self, obj):
        """Export detail field, returning empty string if not set."""
        return obj.detail if obj.detail else ""

    def dehydrate_created_by(self, obj):
        """Export created_by username, returning empty string if not set."""
        return obj.created_by.username if obj.created_by else ""

    def dehydrate_updated_by(self, obj):
        """Export updated_by username, returning empty string if not set."""
        return obj.updated_by.username if obj.updated_by else ""

    def dehydrate_created_at(self, obj):
        """Format created_at for export with i18n support."""
        if obj.created_at:
            try:
                locale.setlocale(locale.LC_TIME, "id_ID.utf8")
            except locale.Error:
                pass  # fallback: will format in English
            
            day = obj.created_at.strftime("%d").lstrip("0")
            month_year = obj.created_at.strftime("%B %Y")
            time = obj.created_at.strftime("%H:%M")
            return f"{day} {month_year}, {time}"
        return ""

    def dehydrate_updated_at(self, obj):
        """Format updated_at for export with i18n support."""
        if obj.updated_at:
            try:
                locale.setlocale(locale.LC_TIME, "id_ID.utf8")
            except locale.Error:
                pass  # fallback: will format in English
            
            day = obj.updated_at.strftime("%d").lstrip("0")
            month_year = obj.updated_at.strftime("%B %Y")
            time = obj.updated_at.strftime("%H:%M")
            return f"{day} {month_year}, {time}"
        return ""

    class Meta:
        model = LabScheduleModel
        skip_unchanged = True
        report_skipped = True
        fields = EXPORT_FIELDS
        export_order = EXPORT_FIELDS
        export_format_types = [AutoFitXLSX]

    def get_queryset(self):
        """Optimize queryset for export with select_related."""
        return (
            super()
            .get_queryset()
            .select_related("created_by")
            .filter(is_active=True)
            .order_by("date", "start_time")
        )
