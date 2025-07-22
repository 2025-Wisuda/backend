"""
Lab Schedule Export View for Django admin.

Provides custom export functionality for lab schedule data with comprehensive
filtering options and security controls.
"""

from datetime import datetime
from typing import Any, Dict

from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _

from core.enums.user_group_enum import UserGroup
from shared.export import BaseExportView
from shared.utils.permission_config_utils import has_group_permission

from ...models import LabScheduleModel
from ..forms.lab_schedule_export_form import LabScheduleExportForm
from ..lab_schedule_resource import LabScheduleResource


class LabScheduleExportView(BaseExportView):
    """
    Lab Schedule export view with filtering and field selection.

    Features:
    - Date range filtering
    - Activity type filtering
    - Source model filtering
    - Field selection
    - Permission controls (lab employees only)
    - Security: no sensitive data exposure
    """

    model = LabScheduleModel
    resource_class = LabScheduleResource
    form_class = LabScheduleExportForm
    template_name = "admin/lab_schedule/labschedulemodel/export_form.html"
    permission_check_method = "_has_lab_employee_permission"
    export_filename_prefix = "lab_schedule"

    def _get_base_queryset(self, request) -> QuerySet:
        """
        Get base queryset with optimizations and security filters.

        - Select related for performance
        - Filter by is_active=True for non-superusers
        - Order by schedule date and time
        """
        queryset = self.model.objects.select_related("created_by", "updated_by")

        # Non-superusers only see active schedules
        if not request.user.is_superuser:
            queryset = queryset.filter(is_active=True)

        return queryset.order_by("date", "start_time")

    def _apply_filters(self, queryset: QuerySet, form_data: Dict[str, Any]) -> QuerySet:
        """Apply filters based on form data."""

        # Base date filtering (created_at) - map to date for lab schedules
        date_from = form_data.get("created_at_from")
        date_to = form_data.get("created_at_to")
        month = form_data.get("created_at_month")
        year = form_data.get("created_at_year")

        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        if month:
            queryset = queryset.filter(date__month=int(month))

        if year:
            queryset = queryset.filter(date__year=int(year))

        # Schedule-specific date filtering (date)
        schedule_from = form_data.get("date_from")
        schedule_to = form_data.get("date_to")
        schedule_month = form_data.get("schedule_month")
        schedule_year = form_data.get("schedule_year")

        if schedule_from:
            queryset = queryset.filter(date__gte=schedule_from)

        if schedule_to:
            queryset = queryset.filter(date__lte=schedule_to)

        if schedule_month:
            queryset = queryset.filter(date__month=int(schedule_month))

        if schedule_year:
            queryset = queryset.filter(date__year=int(schedule_year))

        # Source model filtering - only the 3 source models we support
        source_model = form_data.get("source_model")
        if source_model and source_model in [
            "LabAllocation",
            "CourseSession",
            "RoomBooking",
        ]:
            queryset = queryset.filter(source_model=source_model)

        return queryset

    def _get_template_context(self, request, form) -> Dict[str, Any]:
        """Get template context with lab schedule specific data."""
        context = super()._get_template_context(request, form)

        # Update title for lab schedule
        context.update(
            {
                "title": _("Export Lab Schedules with Filters"),
                "module_name": _("Lab Schedule"),
                "export_description": _(
                    "Export laboratory schedule data with customizable filters and field selection. "
                    "This includes data from all lab booking sources: allocations, course sessions, and room bookings."
                ),
            }
        )

        return context

    def _generate_filename(self, form_data: Dict[str, Any], file_format: str) -> str:
        """Generate filename with descriptive information."""

        # Base filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_parts = [self.export_filename_prefix, timestamp]

        # Add source model if filtered
        source_model = form_data.get("source_model")
        if source_model:
            filename_parts.append(source_model.lower())

        # Add schedule date range if specified
        schedule_from = form_data.get("date_from")
        schedule_to = form_data.get("date_to")
        if schedule_from and schedule_to:
            filename_parts.append(f"schedule_{schedule_from}_{schedule_to}")
        elif schedule_from:
            filename_parts.append(f"schedule_from_{schedule_from}")
        elif schedule_to:
            filename_parts.append(f"schedule_until_{schedule_to}")

        # Add base date range if specified (fallback to created_at mapping)
        if not (schedule_from or schedule_to):
            date_from = form_data.get("created_at_from")
            date_to = form_data.get("created_at_to")
            if date_from and date_to:
                filename_parts.append(f"created_{date_from}_{date_to}")
            elif date_from:
                filename_parts.append(f"created_from_{date_from}")
            elif date_to:
                filename_parts.append(f"created_until_{date_to}")

        return f"{'_'.join(filename_parts)}.{file_format}"

    def _check_permissions(self, request) -> bool:
        """Check if user has lab employee permissions."""
        allowed_groups = [
            UserGroup.LABORATORY_HEAD,
            UserGroup.LABORATORY_TECHNICIAN,
        ]
        return has_group_permission(request.user, allowed_groups)
