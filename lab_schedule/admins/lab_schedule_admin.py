"""
Django admin configuration for Lab Schedule Aggregator.

Provides read-only admin interface for viewing all lab schedules aggregated
from different booking types (LabAllocation, CourseSession, RoomBooking).
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportMixin

from shared.format.custom_xlsx_format import AutoFitXLSX
from shared.utils.permission_config_utils import admin_laboratory_employee_only

from ..models import LabScheduleModel
from .lab_schedule_resource import LabScheduleResource


@admin.register(LabScheduleModel)
class LabScheduleAdmin(ExportMixin, admin.ModelAdmin):
    """
    Simplified read-only admin for Lab Schedule aggregator with export-only functionality.

    This admin provides a view of all lab schedules aggregated from different
    booking types. It's read-only since the actual scheduling is done in the
    source models (LabAllocation, CourseSession, RoomBooking).

    Export functionality allows generating reports of schedule data.
    """

    resource_class = LabScheduleResource

    list_display = [
        "schedule_date",
        "time_display",
        "activity_type",
        "activity_detail_short",
        "source_model",
    ]

    list_filter = [
        "source_model",
        "activity_type",
        "schedule_date",
    ]

    search_fields = [
        "activity_type",
        "activity_detail",
    ]

    readonly_fields = (
        "schedule_date",
        "start_time",
        "end_time",
        "source_model",
        "source_id",
        "activity_type",
        "activity_detail",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    ordering = ["-schedule_date", "-start_time"]
    date_hierarchy = "schedule_date"

    fieldsets = (
        (
            _("Schedule Information"),
            {
                "fields": (
                    "schedule_date",
                    "start_time",
                    "end_time",
                    "activity_type",
                    "activity_detail",
                )
            },
        ),
        (
            _("Source Information"),
            {
                "fields": (
                    "source_model",
                    "source_id",
                ),
                "description": _(
                    "Information about the original booking that created this schedule entry."
                ),
            },
        ),
        (
            _("Important Dates"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Audit Info"),
            {
                "fields": ("created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        """All fields are readonly since this is an aggregator."""
        return self.readonly_fields

    def time_display(self, obj):
        """Display formatted time range."""
        if obj.start_time and obj.end_time:
            return (
                f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
            )
        return "-"

    time_display.short_description = _("Time")

    def activity_detail_short(self, obj):
        """Display shortened activity details."""
        if obj.activity_detail:
            return (
                obj.activity_detail[:50] + "..."
                if len(obj.activity_detail) > 50
                else obj.activity_detail
            )
        return "-"

    activity_detail_short.short_description = _("Details")

    def get_queryset(self, request):
        """
        Optimize queryset with select_related.

        Show all data for superusers.
        For non-superusers, show only entries where is_active=True.
        """
        qs = super().get_queryset(request).select_related("created_by", "updated_by")

        if not request.user.is_superuser:
            qs = qs.filter(is_active=True)

        return qs

    def has_add_permission(self, request):
        """Disable adding since this is an aggregator."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable hard delete - this is a read-only aggregator."""
        return False

    def has_change_permission(self, request, obj=None):
        """No editing allowed - this is a read-only aggregator."""
        return False

    def get_export_formats(self):
        """Export formats available."""
        formats = super().get_export_formats()
        export_formats = [AutoFitXLSX]
        for format_cls in formats:
            if format_cls.__name__ != "XLSX":
                export_formats.append(format_cls)
        return export_formats

    def export_action(self, request, *args, **kwargs):
        """Export action - restricted to lab employees."""
        # Check permissions manually
        if not self._has_lab_employee_permission(request):
            from django.contrib import messages
            from django.shortcuts import redirect

            messages.error(request, _("Only laboratory employees can export data"))
            return redirect(request.META.get("HTTP_REFERER", "admin:index"))
        return super().export_action(request, *args, **kwargs)

    def _has_lab_employee_permission(self, request):
        """Check if user has lab employee permissions."""
        from core.enums.user_group_enum import UserGroup
        from shared.utils.permission_config_utils import has_group_permission

        allowed_groups = [
            UserGroup.LABORATORY_TECHNICIAN,
        ]
        return has_group_permission(request.user, allowed_groups)

    def get_import_formats(self):
        """Disable import - this is export-only."""
        return []

    def has_import_permission(self, request):
        """Disable import - this is export-only."""
        return False
