"""
Lab Schedule admin interface for viewing aggregated lab schedules with export-only functionality.

This module provides a read-only administrative view of all lab schedules,
aggregated from various booking sources like LabAllocation, CourseSession, and RoomBooking.
It emphasizes data integrity by preventing direct CRUD operations on the aggregated data,
as all information is synchronized from the source models.

Key Business Rules:
- Read-only Aggregator: Displays a consolidated view of lab schedules.
- Export-Only: Allows data export with restrictions, no import or direct modification.
- Data Source: Aggregates data from LabAllocation, CourseSession, RoomBooking models.
- Role-Based Access: Export functionality is restricted to authorized lab employees.
- Comprehensive Filtering: The custom export system supports advanced filtering options.

Export Architecture:
- Utilizes `LabScheduleResource` for defining exportable fields and data dehydration.
- Leverages `LabScheduleExportView` for handling the export process with custom filters.
- Ensures consistent field definitions and formatting for exported data.
"""

from core.enums import UserGroup
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportMixin
from shared.utils import (
    AuditFieldMixin,
    EnhancedExportAdminMixin,
    ReadOnlyAggregatorMixin,
    StandardExportFormatMixin,
    SuperuserDataVisibilityMixin,
)

from ..models import LabScheduleModel
from .lab_schedule_resource import LabScheduleResource
from .views.lab_schedule_export_view import LabScheduleExportView


@admin.register(LabScheduleModel)
class LabScheduleAdmin(
    EnhancedExportAdminMixin,
    ReadOnlyAggregatorMixin,
    StandardExportFormatMixin,
    AuditFieldMixin,
    SuperuserDataVisibilityMixin,
    ExportMixin,
    admin.ModelAdmin,
):
    """
    Admin interface for the LabScheduleModel, providing a read-only, export-only view
    of aggregated lab schedules with role-based access control for exports.

    This admin class is designed to display data from `LabScheduleModel`, which acts
    as an aggregator for various lab booking types. Therefore, direct creation,
    modification, or deletion of schedule entries through this interface is disabled.

    Security Features:
    - Read-Only Aggregator: All fields are read-only as data is sourced from other models.
    - Export Restrictions: Export operations are limited to users in specific lab employee groups.
    - Data Visibility: Superusers see all entries; other users see only active entries.
    - No Direct CRUD: `has_add_permission`, `has_change_permission`, `has_delete_permission`
      are overridden to return `False`.

    Export System:
    - Integrates with `django-import-export` via `ExportMixin`.
    - Uses `LabScheduleResource` as `resource_class` to define export fields and behavior.
    - Provides a custom export view (`_export_with_filters_view`) that utilizes
      `LabScheduleExportView` for advanced filtering (e.g., by date range, activity type).
    - The standard export action is overridden to redirect to this custom filtered export.
    """

    resource_class = LabScheduleResource

    # Enhanced export configuration
    export_view_class = LabScheduleExportView
    export_filtered_url_name = "lab_schedule_labschedulemodel_export_filtered"

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)

    list_display = [
        "date",
        "time_display",
        "type",
        "detail_short",
        "source_model",
    ]

    list_filter = [
        "source_model",
        "type",
        "date",
    ]

    search_fields = [
        "type",
        "detail",
    ]

    readonly_fields = (
        "date",
        "start_time",
        "end_time",
        "source_model",
        "source_id",
        "type",
        "detail",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    ordering = ["-date", "-start_time"]
    date_hierarchy = "date"

    fieldsets = (
        (
            _("Schedule Information"),
            {
                "fields": (
                    "date",
                    "start_time",
                    "end_time",
                    "type",
                    "detail",
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
                "classes": ("collapse",),
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

    def time_display(self, obj):
        """Display formatted time range."""
        if obj.start_time and obj.end_time:
            return (
                f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
            )
        return "-"

    time_display.short_description = _("Time")

    def detail_short(self, obj):
        """Display shortened activity details."""
        if obj.detail:
            return obj.detail[:50] + "..." if len(obj.detail) > 50 else obj.detail
        return "-"

    detail_short.short_description = _("Details")

    def get_readonly_fields(self, request, obj=None):
        """All fields are readonly since this is an aggregator."""
        return self.readonly_fields

    def has_module_permission(self, request):
        """Control module access based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group in UserGroup.laboratory_staff_employee_groups():
            return True
        elif request.user.group == UserGroup.LABORATORY_ASSISTANT.value:
            return True

        return False

    def has_view_permission(self, request, obj=None):
        """Control view permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group in UserGroup.laboratory_staff_employee_groups():
            return True
        elif request.user.group == UserGroup.LABORATORY_ASSISTANT.value:
            return True
        return False

    def has_export_permission(self, request):
        """Control export permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group in UserGroup.laboratory_staff_employee_groups():
            return True
        return False
