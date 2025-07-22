"""
Enhanced export admin mixins for consistent export functionality across admin interfaces.

Provides reusable components for admin classes that need advanced export capabilities
with permission controls and custom filtering.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from shared.utils.permission_config_utils import admin_laboratory_employee_only

from .admin_permission_mixins import (
    LabEmployeePermissionMixin,
    StandardExportFormatMixin,
)


class EnhancedExportAdminMixin(LabEmployeePermissionMixin, StandardExportFormatMixin):
    """
    Mixin that provides enhanced export functionality with permission controls.

    Features:
    - Laboratory employee permission validation
    - Custom export URLs
    - Standardized export formats
    - Export view delegation pattern

    Usage:
        class MyAdmin(EnhancedExportAdminMixin, admin.ModelAdmin):
            export_view_class = MyExportView  # Required
            export_filtered_url_name = 'myapp_mymodel_export_filtered'  # Required
    """

    # Subclasses must define these attributes
    export_view_class = None
    export_filtered_url_name = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.export_view_class:
            self.export_view = self.export_view_class(self)

    def get_urls(self):
        """Add custom URLs for export functionality."""
        urls = super().get_urls()
        if self.export_filtered_url_name:
            custom_urls = [
                path(
                    "export-filtered/",
                    self.admin_site.admin_view(self.export_with_filters),
                    name=self.export_filtered_url_name,
                ),
            ]
            return custom_urls + urls
        return urls

    def export_with_filters(self, request, queryset=None):
        """Export with advanced filtering options - delegate to export view."""
        if hasattr(self, "export_view") and self.export_view:
            return self.export_view.export_action(request, queryset)
        return self._fallback_export(request, queryset)

    def export_action(self, request, *args, **kwargs):
        """
        Override default export with enhanced filtered export.

        Redirects to custom export form with advanced features:
        - Date range filtering
        - Custom field filtering
        - Dynamic field selection
        - Centralized field definitions (no duplication)
        """
        if not self._has_lab_employee_permission(request):
            messages.error(request, _("Only laboratory employees can export data"))
            return redirect(request.META.get("HTTP_REFERER", "admin:index"))

        if self.export_filtered_url_name:
            return redirect(reverse(f"admin:{self.export_filtered_url_name}"))

        # Fallback to standard export
        return super().export_action(request, *args, **kwargs)

    def _fallback_export(self, request, queryset):
        """Fallback export method if no export view is configured."""
        return super().export_action(request, *args, **kwargs) # type: ignore

    export_with_filters.short_description = _("Export with Filters")


class LabEmployeeRestrictedActionsMixin(LabEmployeePermissionMixin):
    """
    Mixin for admin classes that need to restrict certain actions to lab employees.

    Provides decorators and validation for lab employee-only operations.
    """

    def process_import(self, request, *args, **kwargs):
        """Restrict import operations to lab employees only."""
        if not self._has_lab_employee_permission(request):
            messages.error(request, _("Only laboratory employees can import data"))
            return redirect(request.META.get("HTTP_REFERER", "admin:index"))
        return super().process_import(request, *args, **kwargs)

    def _validate_lab_employee_action(self, request, action_name):
        """
        Helper method to validate lab employee permission for any action.

        Args:
            request: Django request object
            action_name: Name of the action for error message

        Returns:
            bool: True if user has permission, False otherwise
        """
        if not self._has_lab_employee_permission(request):
            messages.error(
                request,
                _("Only laboratory employees can perform {action}").format(
                    action=action_name
                ),
            )
            return False
        return True


class BulkActionsMixin:
    """
    Mixin that provides standardized bulk action patterns.

    Provides helper methods for creating consistent bulk actions with proper messaging.
    """

    def _create_bulk_activate_action(self, model_name, superuser_only=False):
        """Create standardized activate action."""
        from shared.utils import create_activate_action

        return create_activate_action(
            model_name=model_name,
            superuser_only=superuser_only,
            verbose_name=_("Restore Selected {models}").format(
                models=model_name.title()
            ),
        )

    def _create_bulk_deactivate_action(self, model_name, superuser_only=False):
        """Create standardized deactivate action."""
        from shared.utils import create_deactivate_action

        return create_deactivate_action(
            model_name=model_name,
            superuser_only=superuser_only,
            verbose_name=_("Delete Selected {models}").format(
                models=model_name.title()
            ),
        )

    def _execute_bulk_action(
        self, request, queryset, action_func, success_message_template
    ):
        """
        Execute bulk action with standardized messaging.

        Args:
            request: Django request object
            queryset: QuerySet to operate on
            action_func: Function to execute (should return count)
            success_message_template: Message template with {count} placeholder
        """
        try:
            count = action_func(queryset)
            if count > 0:
                messages.success(request, success_message_template.format(count=count))
            else:
                messages.info(request, _("No items needed to be processed."))
        except Exception as e:
            messages.error(
                request, _("Error during bulk operation: {error}").format(error=str(e))
            )
