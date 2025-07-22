"""
Group Admin Configuration

Django admin interface for group/permission management.
Provides read-only access to Django's built-in Group model with enhanced display.
"""

from core.enums import UserGroup
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _


class GroupProxy(Group):
    """
    Proxy model for Group to customize admin interface.
    Provides enhanced metadata without altering the original model.
    """

    class Meta:
        proxy = True
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        app_label = "custom_auth"


class GroupAdmin(BaseGroupAdmin):
    """
    Enhanced admin interface for Django Groups.

    Features:
    - Read-only access for laboratory staff
    - Permission count display
    - Enhanced security with controlled access
    - Integrated with custom user management
    """

    model = GroupProxy

    def has_module_permission(self, request):
        """Control module access based on user role."""
        if request.user.is_superuser:
            return True
        return False

    def has_view_permission(self, request, obj=None):
        """Control view permission based on user role."""
        if request.user.is_superuser:
            return True
        return False

    def has_add_permission(self, request):
        """Control add permission based on user role."""
        if request.user.is_superuser:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """Control delete permission based on user role."""
        if request.user.is_superuser:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """Control change permission based on user role."""
        if request.user.is_superuser:
            return True
        return False

    def has_export_permission(self, request):
        """Control export permission based on user role."""
        if request.user.is_superuser:
            return True
        return False

    def has_import_permission(self, request):
        """Control import permission based on user role."""
        if request.user.is_superuser:
            return True
        return False

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if "name" not in readonly_fields:
            readonly_fields.append("name")
        return readonly_fields

    def get_fieldsets(self, request, obj=None):
        return (
            (
                None,
                {
                    "fields": ("name",),
                    "description": _("Group name cannot be changed"),
                },
            ),
            (
                _("Permissions"),
                {
                    "fields": ("permissions",),
                    "description": _("Only superusers can edit permissions"),
                },
            ),
        )

    list_display = ("name", "permission_count")
    search_fields = ("name",)
    ordering = ("name",)

    def permission_count(self, obj):
        """Display the number of permissions assigned to the group."""
        return obj.permissions.count()

    permission_count.short_description = _("Permission Count")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["title"] = _("User Groups - Only permissions can be edited")
        return super().changelist_view(request, extra_context)


admin.site.unregister(Group)
admin.site.register(GroupProxy, GroupAdmin)
