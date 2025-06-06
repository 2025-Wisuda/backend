"""
Django admin configuration for Group management.

This module customizes the Django admin interface for managing user groups,
providing controlled access and preventing unauthorized modifications to
system-critical groups. Groups are displayed under "User Management" section.
"""

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _


class GroupProxy(Group):
    """Proxy model to display groups under User Management section."""

    class Meta:
        proxy = True
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        app_label = "custom_auth"


class GroupAdmin(BaseGroupAdmin):
    model = GroupProxy

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if "name" not in readonly_fields:
            readonly_fields.append("name")
        return readonly_fields

    def get_fieldsets(self, request, obj=None):
        if obj:
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
        return super().get_fieldsets(request, obj)

    def save_model(self, request, obj, form, change):
        if change:
            original = Group.objects.get(pk=obj.pk)
            obj.name = original.name
        super().save_model(request, obj, form, change)

    list_display = ("name", "permission_count")
    search_fields = ("name",)
    ordering = ("name",)

    def permission_count(self, obj):
        return obj.permissions.count()

    permission_count.short_description = _("Permission Count")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["title"] = _("User Groups - Only permissions can be edited")
        return super().changelist_view(request, extra_context)


admin.site.unregister(Group)
admin.site.register(GroupProxy, GroupAdmin)
