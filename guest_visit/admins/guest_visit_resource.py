"""
Guest Visit resource for import/export operations.

Defines the fields and dehydration methods for exporting guest visit data.
"""

from django.utils.translation import gettext_lazy as _
from import_export import fields, resources

from ..models import GuestVisitModel


class GuestVisitResource(resources.ModelResource):
    """
    Resource for guest visit data export.

    Provides field mapping and data transformation for export operations.
    """

    # Define exportable fields with custom headers
    EXPORT_FIELDS = [
        "date",
        "start_time",
        "end_time",
        "visitor_name",
        "identity_type",
        "identity_number",
        "purpose",
        "created_at",
        "created_by",
    ]

    # Custom field definitions
    visitor_name = fields.Field(
        column_name=_("Visitor Name"), attribute="get_visitor_name"
    )

    identity_type = fields.Field(
        column_name=_("Identity Type"), attribute="identity_type"
    )

    identity_number = fields.Field(
        column_name=_("Identity Number"), attribute="identity_number"
    )

    date = fields.Field(column_name=_("Visit Date"), attribute="date")

    start_time = fields.Field(column_name=_("Start Time"), attribute="start_time")

    end_time = fields.Field(column_name=_("End Time"), attribute="end_time")

    purpose = fields.Field(column_name=_("Purpose"), attribute="purpose")

    created_at = fields.Field(column_name=_("Created At"), attribute="created_at")

    created_by = fields.Field(column_name=_("Created By"), attribute="created_by")

    class Meta:
        model = GuestVisitModel
        fields = (
            "date",
            "start_time",
            "end_time",
            "visitor_name",
            "identity_type",
            "identity_number",
            "purpose",
            "created_at",
            "created_by",
        )
        export_order = (
            "date",
            "start_time",
            "end_time",
            "visitor_name",
            "identity_type",
            "identity_number",
            "purpose",
            "created_at",
            "created_by",
        )
        skip_unchanged = True
        report_skipped = False
        import_id_fields = []  # No import allowed - export only

    def dehydrate_created_by(self, guest_visit):
        """Format created by user display."""
        if guest_visit.created_by:
            return f"{guest_visit.created_by.first_name} {guest_visit.created_by.last_name}"
        return ""

    def dehydrate_start_time(self, guest_visit):
        """Format start time."""
        if guest_visit.start_time:
            return guest_visit.start_time.strftime("%H:%M")
        return ""

    def dehydrate_end_time(self, guest_visit):
        """Format end time."""
        if guest_visit.end_time:
            return guest_visit.end_time.strftime("%H:%M")
        return ""

    def dehydrate_identity_type(self, guest_visit):
        """Format identity type display."""
        if guest_visit.identity_type:
            return guest_visit.get_identity_type_display()
        return ""
