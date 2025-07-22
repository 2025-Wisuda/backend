from django.utils.translation import gettext_lazy as _
from import_export import fields, resources

from ..models import RoomBookingModel


class RoomBookingResource(resources.ModelResource):
    booker = fields.Field(
        column_name=_("Booker"),
        attribute="booker",
    )

    booking_type = fields.Field(
        column_name=_("Booking Type"),
        attribute="booking_type",
    )

    purpose = fields.Field(
        column_name=_("Purpose"),
        attribute="purpose",
    )

    seminar_type = fields.Field(
        column_name=_("Seminar Type"),
        attribute="seminar_type",
    )

    research_title = fields.Field(
        column_name=_("Research Title"),
        attribute="research_title",
    )

    supervisor_main = fields.Field(
        column_name=_("Main Supervisor"),
        attribute="supervisor_main",
    )

    supervisor_secondary = fields.Field(
        column_name=_("Secondary Supervisor"),
        attribute="supervisor_secondary",
    )

    examiner = fields.Field(
        column_name=_("Examiner"),
        attribute="examiner",
    )

    document_proof = fields.Field(
        column_name=_("Document Proof"),
        attribute="document_proof",
    )

    date = fields.Field(
        column_name=_("Booking Date"),
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

    approval_status = fields.Field(
        column_name=_("Booking Approval Status"),
        attribute="approval_status",
    )

    approved_by_user = fields.Field(
        column_name=_("Approved By User"),
        attribute="approved_by_user",
    )

    approval_timestamp = fields.Field(
        column_name=_("Approval Timestamp"),
        attribute="approval_timestamp",
    )

    approval_notes = fields.Field(
        column_name=_("Approval Notes"),
        attribute="approval_notes",
    )

    def dehydrate_date(self, obj):
        """Format date with i18n-ready month names."""
        from django.utils.translation import gettext as _

        month_names = {
            1: _("January"),
            2: _("February"),
            3: _("March"),
            4: _("April"),
            5: _("May"),
            6: _("June"),
            7: _("July"),
            8: _("August"),
            9: _("September"),
            10: _("October"),
            11: _("November"),
            12: _("December"),
        }
        dt = obj.date
        return f"{dt.day} {month_names[dt.month]} {dt.year}"

    def dehydrate_start_time(self, obj):
        return obj.start_time.strftime("%H:%M") if obj.start_time else ""

    def dehydrate_end_time(self, obj):
        return obj.end_time.strftime("%H:%M") if obj.end_time else ""

    def dehydrate_booker(self, obj):
        # Tampilkan username atau full name kalau ada
        if obj.booker.get_full_name():
            return obj.booker.get_full_name()
        return obj.booker.username

    def dehydrate_approved_by_user(self, obj):
        if obj.approved_by_user:
            if obj.approved_by_user.get_full_name():
                return obj.approved_by_user.get_full_name()
            return obj.approved_by_user.username
        return ""

    def dehydrate_document_proof(self, obj):
        # Kalau ada dokumen, tampilkan URL-nya
        if obj.document_proof:
            return obj.document_proof.url
        return ""

    def dehydrate_approval_timestamp(self, obj):
        """Format approval timestamp with i18n-ready format."""
        from django.utils.translation import gettext as _

        if obj.approval_timestamp:
            # Use i18n-ready format: "20 July 2025, 15:30"
            return obj.approval_timestamp.strftime(_("%d %B %Y, %H:%M"))
        return ""

    class Meta:
        model = RoomBookingModel
        skip_unchanged = True
        report_skipped = True
        fields = (
            "booker",
            "booking_type",
            "purpose",
            "seminar_type",
            "research_title",
            "supervisor_main",
            "supervisor_secondary",
            "examiner",
            "document_proof",
            "date",
            "start_time",
            "end_time",
            "approval_status",
            "approved_by_user",
            "approval_timestamp",
            "approval_notes",
        )
        export_order = fields
