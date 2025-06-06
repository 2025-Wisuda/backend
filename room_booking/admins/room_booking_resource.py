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

    booking_date = fields.Field(
        column_name=_("Booking Date"),
        attribute="booking_date",
    )

    booking_start_time = fields.Field(
        column_name=_("Start Time"),
        attribute="booking_start_time",
    )

    booking_end_time = fields.Field(
        column_name=_("End Time"),
        attribute="booking_end_time",
    )

    booking_approval_status = fields.Field(
        column_name=_("Booking Approval Status"),
        attribute="booking_approval_status",
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

    def dehydrate_booking_date(self, obj):
        month = {
            1: "Januari",
            2: "Februari",
            3: "Maret",
            4: "April",
            5: "Mei",
            6: "Juni",
            7: "Juli",
            8: "Agustus",
            9: "September",
            10: "Oktober",
            11: "November",
            12: "Desember",
        }
        dt = obj.booking_date
        return f"{dt.day} {month[dt.month]} {dt.year}"

    def dehydrate_booking_start_time(self, obj):
        return (
            obj.booking_start_time.strftime("%H:%M") if obj.booking_start_time else ""
        )

    def dehydrate_booking_end_time(self, obj):
        return obj.booking_end_time.strftime("%H:%M") if obj.booking_end_time else ""

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
        if obj.approval_timestamp:
            return obj.approval_timestamp.strftime("%d %b %Y %H:%M")
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
            "booking_date",
            "booking_start_time",
            "booking_end_time",
            "booking_approval_status",
            "approved_by_user",
            "approval_timestamp",
            "approval_notes",
        )
        export_order = fields
