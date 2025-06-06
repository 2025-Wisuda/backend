import locale

from django.utils.translation import gettext_lazy as _
from import_export import fields, resources

from ..models import LabScheduleModel


class LabScheduleResource(resources.ModelResource):
    """
    Export-only resource for Lab Schedule aggregator data.

    Exports essential schedule information for reporting purposes.
    No import functionality since this is a read-only aggregator.
    """

    activity_type = fields.Field(
        column_name=_("Activity Type"),
        attribute="activity_type",
    )

    schedule_date = fields.Field(
        column_name=_("Schedule Date"),
        attribute="schedule_date",
    )

    start_time = fields.Field(
        column_name=_("Start Time"),
        attribute="start_time",
    )

    end_time = fields.Field(
        column_name=_("End Time"),
        attribute="end_time",
    )

    def dehydrate_schedule_date(self, obj):
        """
        Format schedule_date as '4 Juni 2025'.
        Falls back to default locale if Indonesian locale not found.
        """
        date = obj.schedule_date
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

    class Meta:
        model = LabScheduleModel
        skip_unchanged = True
        report_skipped = True
        fields = (
            "activity_type",
            "schedule_date",
            "start_time",
            "end_time",
        )
        export_order = (
            "activity_type",
            "schedule_date",
            "start_time",
            "end_time",
        )

    def get_queryset(self):
        """Optimize queryset for export with select_related."""
        return (
            super()
            .get_queryset()
            .select_related("created_by")
            .filter(is_active=True)
            .order_by("schedule_date", "start_time")
        )
