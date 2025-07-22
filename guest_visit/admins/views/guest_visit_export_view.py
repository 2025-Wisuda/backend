"""
Guest Visit Export View for Django admin.

Provides custom export functionality for guest visit data with comprehensive
filtering options and security controls.
"""

from datetime import datetime
from typing import Any, Dict

from core.enums.user_group_enum import UserGroup
from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _
from shared.export import BaseExportView
from shared.utils.permission_config_utils import has_group_permission

from ...models import GuestVisitModel
from ..forms.guest_visit_export_form import GuestVisitExportForm
from ..guest_visit_resource import GuestVisitResource

User = get_user_model()


class GuestVisitExportView(BaseExportView):
    """
    Guest Visit export view with filtering and field selection.

    Features:
    - Date range filtering
    - Visitor identity type filtering
    - Host user filtering
    - Field selection
    - Permission controls (lab employees only)
    - Security: no sensitive data exposure
    """

    model = GuestVisitModel
    resource_class = GuestVisitResource
    form_class = GuestVisitExportForm
    template_name = "admin/guest_visit/guestvisitmodel/export_form.html"
    permission_check_method = "_has_lab_employee_permission"
    export_filename_prefix = "guest_visits"

    def _get_base_queryset(self, request) -> QuerySet:
        """
        Get base queryset with optimizations and security filters.

        - Select related for performance
        - Filter by is_active=True for non-superusers
        - Order by visit date and time
        """
        queryset = self.model.objects.select_related(
            "visitor", "created_by", "updated_by"
        )

        # Non-superusers only see active visits
        if not getattr(request.user, "is_superuser", False):
            queryset = queryset.filter(is_active=True)

        return queryset.order_by("date", "start_time")

    def _apply_filters(self, queryset: QuerySet, form_data: Dict[str, Any]) -> QuerySet:
        """Apply filters based on form data."""

        # Base date filtering (created_at)
        date_from = form_data.get("created_at_from")
        date_to = form_data.get("created_at_to")
        month = form_data.get("created_at_month")
        year = form_data.get("created_at_year")

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        if month:
            queryset = queryset.filter(created_at__month=int(month))

        if year:
            queryset = queryset.filter(created_at__year=int(year))

        # Visit-specific date filtering (date)
        visit_from = form_data.get("visit_date_from")
        visit_to = form_data.get("visit_date_to")
        visit_month = form_data.get("visit_month")
        visit_year = form_data.get("visit_year")

        if visit_from:
            queryset = queryset.filter(date__gte=visit_from)

        if visit_to:
            queryset = queryset.filter(date__lte=visit_to)

        if visit_month:
            queryset = queryset.filter(date__month=int(visit_month))

        if visit_year:
            queryset = queryset.filter(date__year=int(visit_year))

        # Visitor identity type filtering
        identity_type = form_data.get("visitor_identity_type")
        if identity_type:
            queryset = queryset.filter(identity_type=identity_type)

        # Created By filtering
        host_user_id = form_data.get("host_user")
        if host_user_id:
            try:
                host_user = User.objects.get(id=host_user_id)
                queryset = queryset.filter(created_by=host_user)
            except User.DoesNotExist:
                pass

        return queryset

    def _get_template_context(self, request, form) -> Dict[str, Any]:
        """Get template context with guest visit specific data."""
        context = super()._get_template_context(request, form)

        # Update title for guest visit
        context.update(
            {
                "title": _("Export Guest Visits with Filters"),
                "module_name": _("Guest Visit"),
                "export_description": _(
                    "Export guest visit data with customizable filters and field selection. "
                    "This includes visitor information, visit details, and host assignments."
                ),
            }
        )

        return context

    def _generate_filename(self, form_data: Dict[str, Any], file_format: str) -> str:
        """Generate filename with descriptive information."""

        # Base filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_parts = [self.export_filename_prefix, timestamp]

        # Add identity type if filtered
        identity_type = form_data.get("visitor_identity_type")
        if identity_type:
            filename_parts.append(identity_type.lower())

        # Add visit date range if specified
        visit_from = form_data.get("visit_date_from")
        visit_to = form_data.get("visit_date_to")
        if visit_from and visit_to:
            filename_parts.append(f"visit_{visit_from}_{visit_to}")
        elif visit_from:
            filename_parts.append(f"visit_from_{visit_from}")
        elif visit_to:
            filename_parts.append(f"visit_until_{visit_to}")

        # Add base date range if specified (fallback to created_at)
        if not (visit_from or visit_to):
            date_from = form_data.get("created_at_from")
            date_to = form_data.get("created_at_to")
            if date_from and date_to:
                filename_parts.append(f"created_{date_from}_{date_to}")
            elif date_from:
                filename_parts.append(f"created_from_{date_from}")
            elif date_to:
                filename_parts.append(f"created_until_{date_to}")

        # Add host user if filtered
        host_user_id = form_data.get("host_user")
        if host_user_id:
            try:
                host_user = User.objects.get(id=host_user_id)
                host_name = f"{host_user.first_name}_{host_user.last_name}".lower()
                filename_parts.append(f"host_{host_name}")
            except User.DoesNotExist:
                pass

        return f"{'_'.join(filename_parts)}.{file_format}"

    def _check_permissions(self, request) -> bool:
        """Check if user has lab employee permissions."""
        allowed_groups = [
            UserGroup.LABORATORY_HEAD,
            UserGroup.LABORATORY_TECHNICIAN,
        ]
        return has_group_permission(request.user, allowed_groups)
