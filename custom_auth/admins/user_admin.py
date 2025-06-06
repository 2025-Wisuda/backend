"""User management admin interface - simplified approach."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportMixin

from shared.format.custom_xlsx_format import AutoFitXLSX
from shared.utils import (
    admin_laboratory_employee_only,
    create_activate_action,
    create_deactivate_action,
)

from ..models import CustomUserModel
from .user_resource import UserResource

User = get_user_model()


class UserAdminForm(UserChangeForm):
    """Custom form for editing users in admin."""

    class Meta:
        model = CustomUserModel
        fields = "__all__"


@admin.register(CustomUserModel)
class UserAdmin(ImportExportMixin, BaseUserAdmin):
    form = UserAdminForm
    add_form_template = "admin/auth/add_form.html"
    resource_class = UserResource
    model = CustomUserModel

    list_display = (
        "username",
        "first_name",
        "last_name",
        "group",
        "is_staff",
    )

    list_filter = ("group",)

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "student_number",
        "employee_number",
    )

    ordering = ("username", "first_name", "last_name")

    add_fieldsets = (
        (
            _("Account Authentication"),
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
                "description": _("Create login credentials for the new user."),
            },
        ),
        (
            _("Basic Information"),
            {
                "classes": ("wide",),
                "fields": ("first_name", "last_name", "group"),
                "description": _("Set basic user information and role."),
            },
        ),
        (
            _("Identity Numbers"),
            {
                "classes": ("wide",),
                "fields": ("student_number", "employee_number"),
                "description": _("Enter appropriate ID number based on role."),
            },
        ),
    )
    fieldsets = (
        (_("Authentication"), {"fields": ("username", "password")}),
        (
            _("Permissions"),
            {
                "fields": ("groups",),
                "description": _(
                    "Manage user access and permissions in the admin panel."
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Face Recognition"),
            {
                "fields": ("face_uploaded",),
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

    readonly_fields = (
        "face_uploaded",
        "last_login",
        "date_joined",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    def get_readonly_fields(self, request, obj=None):
        """Make username readonly only when editing existing user, not when adding new user."""
        readonly = list(self.readonly_fields)
        if obj:
            readonly.append("username")
        return readonly

    def get_queryset(self, request):
        """
        Optimize queryset with select_related.

        Show all data for superuser.
        For others, exclude superusers and show only active entries.
        """
        queryset = (
            super().get_queryset(request).select_related("created_by", "updated_by")
        )

        if request.user.is_superuser:
            return queryset

        return queryset.filter(is_active=True).exclude(is_superuser=True)

    def save_model(self, request, obj, form, change):
        """Set created_by/updated_by fields."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_export_formats(self):
        """Export formats available."""
        formats = super().get_export_formats()
        export_formats = [AutoFitXLSX]
        for format_cls in formats:
            if format_cls.__name__ != "XLSX":
                export_formats.append(format_cls)
        return export_formats

    def process_import(self, request, *args, **kwargs):
        """Import process - restricted to lab employees only."""
        # Check permissions manually
        if not self._has_lab_employee_permission(request):
            from django.contrib import messages
            from django.shortcuts import redirect

            messages.error(request, _("Only laboratory employees can import data"))
            return redirect(request.META.get("HTTP_REFERER", "admin:index"))
        return super().process_import(request, *args, **kwargs)

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
            UserGroup.LABORATORY_HEAD,
            UserGroup.LABORATORY_TECHNICIAN,
        ]
        return has_group_permission(request.user, allowed_groups)

    def activate_users(self, request, queryset):
        """Restore selected users - restricted to lab employees."""
        activate_action = create_activate_action(
            model_name="user",
            superuser_only=True,
            verbose_name=_("Restore Selected Users"),
        )
        return activate_action(self, request, queryset)

    activate_users.short_description = _("Restore Selected Users")

    @admin_laboratory_employee_only
    def deactivate_users(self, request, queryset):
        """Delete selected users - restricted to lab employees."""
        deactivate_action = create_deactivate_action(
            model_name="user",
            superuser_only=False,
            verbose_name=_("Delete Selected Users"),
        )
        return deactivate_action(self, request, queryset)

    deactivate_users.short_description = _("Delete Selected Users")

    def get_actions(self, request):
        """Control actions - remove hard delete, keep soft delete."""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    actions = ["activate_users", "deactivate_users"]

    def has_delete_permission(self, request, obj=None):
        """No hard delete - only soft delete via actions."""
        return False
