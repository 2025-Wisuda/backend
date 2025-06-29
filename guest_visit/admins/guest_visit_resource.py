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
        "visit_date",
        "start_time", 
        "end_time",
        "visitor_name",
        "visitor_identity_type",
        "visitor_identity",
        "purpose",
        "host_user",
        "paraf",
        "created_at",
        "created_by",
    ]
    
    # Custom field definitions
    visitor_name = fields.Field(
        column_name=_("Visitor Name"),
        attribute="get_visitor_name"
    )
    
    visitor_identity_type = fields.Field(
        column_name=_("Identity Type"),
        attribute="visitor_identity_type"
    )
    
    visitor_identity = fields.Field(
        column_name=_("Identity Number"),
        attribute="visitor_identity"
    )
    
    visit_date = fields.Field(
        column_name=_("Visit Date"),
        attribute="date"
    )
    
    start_time = fields.Field(
        column_name=_("Start Time"),
        attribute="start_time"
    )
    
    end_time = fields.Field(
        column_name=_("End Time"),
        attribute="end_time"
    )
    
    purpose = fields.Field(
        column_name=_("Purpose"),
        attribute="purpose"
    )
    
    host_user = fields.Field(
        column_name=_("Host"),
        attribute="staff"
    )
    
    paraf = fields.Field(
        column_name=_("Signature"),
        attribute="paraf"
    )
    
    created_at = fields.Field(
        column_name=_("Created At"),
        attribute="created_at"
    )
    
    created_by = fields.Field(
        column_name=_("Created By"),
        attribute="created_by"
    )

    class Meta:
        model = GuestVisitModel
        fields = (
            "visit_date",
            "start_time", 
            "end_time",
            "visitor_name",
            "visitor_identity_type",
            "visitor_identity",
            "purpose",
            "host_user",
            "paraf",
            "created_at",
            "created_by",
        )
        export_order = (
            "visit_date",
            "start_time", 
            "end_time",
            "visitor_name",
            "visitor_identity_type",
            "visitor_identity",
            "purpose",
            "host_user",
            "paraf",
            "created_at",
            "created_by",
        )
        skip_unchanged = True
        report_skipped = False
        import_id_fields = []  # No import allowed - export only
        
    def dehydrate_host_user(self, guest_visit):
        """Format host user display."""
        if guest_visit.staff:
            return f"{guest_visit.staff.first_name} {guest_visit.staff.last_name}"
        return ""
        
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
        
    def dehydrate_visitor_identity_type(self, guest_visit):
        """Format identity type display."""
        if guest_visit.visitor_identity_type:
            return guest_visit.get_visitor_identity_type_display()
        return "" 