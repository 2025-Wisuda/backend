"""
Reusable admin permission mixins and utilities.

Provides common permission validation patterns used across Django admin interfaces.
"""

from core.enums.user_group_enum import UserGroup
from shared.utils.permission_config_utils import has_group_permission


class LabEmployeePermissionMixin:
    """
    Mixin for admin classes that need laboratory employee permission validation.

    Provides a standardized way to check if user belongs to laboratory employee groups.
    """

    def _has_lab_employee_permission(self, request):
        """
        Validate if user belongs to laboratory employee groups.

        This method can be used consistently across all admin classes that need
        to restrict operations to laboratory employees only.

        Args:
            request: Django request object

        Returns:
            bool: True if user has lab employee permissions, False otherwise
        """
        allowed_groups = [
            UserGroup.LABORATORY_HEAD,
            UserGroup.LABORATORY_TECHNICIAN,
        ]
        return has_group_permission(request.user, allowed_groups)


class ReadOnlyAggregatorMixin:
    """
    Mixin for admin classes that represent read-only data aggregators.

    Disables add, change, delete, and import permissions since the data
    is sourced from other models.
    """

    def has_add_permission(self, request):
        """Disable adding since this is an aggregator."""
        return False

    def has_change_permission(self, request, obj=None):
        """No editing allowed - this is a read-only aggregator."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable hard delete - this is a read-only aggregator."""
        return False

    def get_import_formats(self):
        """Disable import - this is export-only."""
        return []

    def has_import_permission(self, request):
        """Disable import - this is export-only."""
        return False


class SoftDeleteAdminMixin:
    """
    Mixin for admin classes that use soft delete pattern.

    Provides standardized soft delete actions and disables hard delete.
    """

    def has_delete_permission(self, request, obj=None):
        """Disable hard delete - use soft delete actions instead."""
        return False

    def get_actions(self, request):
        """Remove hard delete action, keep soft delete actions."""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


class ExportOnlyMixin:
    """
    Mixin for admin classes that are export-only (no import functionality).
    """

    def get_import_formats(self):
        """Disable import - this is export-only."""
        return []

    def has_import_permission(self, request):
        """Disable import - this is export-only."""
        return False


class StandardExportFormatMixin:
    """
    Mixin that provides standardized export formats with AutoFitXLSX prioritized.
    """

    def get_export_formats(self):
        """Prioritize AutoFitXLSX format over standard XLSX."""
        from shared.format.custom_xlsx_format import AutoFitXLSX

        formats = super().get_export_formats()
        export_formats = [AutoFitXLSX]
        for format_cls in formats:
            if format_cls.__name__ != "XLSX":
                export_formats.append(format_cls)
        return export_formats


class AuditFieldMixin:
    """
    Mixin for admin classes that need to handle audit fields (created_by, updated_by).
    """

    def save_model(self, request, obj, form, change):
        """Auto-populate audit fields with current user."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class SuperuserDataVisibilityMixin:
    """
    Mixin for admin classes that need different data visibility based on user role.

    Superusers see all data, regular users see only active records.
    """

    def get_queryset(self, request):
        """
        Data visibility control based on user privileges.

        Superusers: See all data
        Regular users: Only see active records (is_active=True)
        """
        qs = super().get_queryset(request).select_related("created_by", "updated_by")

        if not request.user.is_superuser:
            qs = qs.filter(is_active=True)

        return qs
