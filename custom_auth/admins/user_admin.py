"""
User Admin Configuration

Django admin interface for user management with enhanced features.
Includes export functionality, audit trails, and role-based field management.
"""

from core.enums import UserGroup
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportMixin
from shared.utils import (
    AuditFieldMixin,
    EnhancedExportAdminMixin,
    SoftDeleteAdminMixin,
    SuperuserDataVisibilityMixin,
    admin_laboratory_employee_only,
    create_activate_action,
    create_deactivate_action,
)

from ..models import CustomUserModel
from .user_resource import UserResource
from .views.user_export_view import UserExportView

User = get_user_model()


class UserAdminForm(UserChangeForm):
    """
    Custom form for user administration with model-specific validation.
    """

    class Meta:
        model = CustomUserModel
        fields = "__all__"

    def clean(self):
        """
        Custom form validation that handles errors gracefully.
        """
        cleaned_data = super().clean()

        try:
            # Create a temporary instance to validate
            if self.instance.pk:
                # For existing instances, update with form data
                for field, value in cleaned_data.items():
                    if hasattr(self.instance, field):
                        setattr(self.instance, field, value)
            else:
                # For new instances, create with form data
                self.instance = self.Meta.model(**cleaned_data)

            # Run model validation
            self.instance.full_clean()

        except ValidationError as e:
            # Add validation errors to form
            for field, error in e.error_dict.items():
                if field in self.fields:
                    self.add_error(field, error)
                else:
                    self.add_error(None, error)

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter group choices based on existing data
        if self.instance and self.instance.pk:
            if self.instance.student_number:
                # If has student_number, only allow student groups
                self.fields["group"].choices = [
                    choice
                    for choice in self.fields["group"].choices
                    if choice[0] in UserGroup.student_groups()
                ]
            elif self.instance.employee_number:
                # If has employee_number, only allow staff groups
                self.fields["group"].choices = [
                    choice
                    for choice in self.fields["group"].choices
                    if choice[0] in UserGroup.staff_groups()
                ]


@admin.register(CustomUserModel)
class UserAdmin(
    EnhancedExportAdminMixin,
    AuditFieldMixin,
    SoftDeleteAdminMixin,
    SuperuserDataVisibilityMixin,
    ImportExportMixin,
    BaseUserAdmin,
):
    """
    Enhanced Django admin for user management.

    Features:
    - Role-based field organization
    - Export functionality with filtering
    - Audit trail display
    - Bulk activation/deactivation
    - Laboratory employee access control

    Field Organization:
    - Authentication: Login credentials
    - Basic Information: Name and role
    - Identity Numbers: Student/Employee IDs (role-dependent)
    - Images: Avatar and face recognition
    - Permissions: Admin access control
    - Audit: Creation/modification tracking
    """

    form = UserAdminForm
    add_form_template = "admin/auth/add_form.html"
    change_list_template = "admin/custom_auth/customusermodel/change_list.html"
    resource_class = UserResource
    model = CustomUserModel
    export_view_class = UserExportView
    export_filtered_url_name = "custom_auth_customusermodel_export_filtered"

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
                "fields": ("group",),
                "description": _(
                    "Manage user access and permissions in the admin panel."
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

    readonly_fields = (
        "last_login",
        "date_joined",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:
            readonly.append("username")
        return readonly

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if not request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True)

        return queryset

    def activate_users(self, request, queryset):
        activate_action = create_activate_action(
            model_name="user",
            superuser_only=True,
            verbose_name=_("Restore Selected Users"),
        )
        return activate_action(self, request, queryset)

    activate_users.short_description = _("Restore Selected Users")

    @admin_laboratory_employee_only
    def deactivate_users(self, request, queryset):
        deactivate_action = create_deactivate_action(
            model_name="user",
            superuser_only=False,
            verbose_name=_("Delete Selected Users"),
        )
        return deactivate_action(self, request, queryset)

    deactivate_users.short_description = _("Delete Selected Users")

    def get_actions(self, request):
        """
        Return actions based on user role.
        """
        actions = super().get_actions(request)

        if request.user.is_superuser:
            actions["activate_users"] = self.get_action("activate_users")
            actions["deactivate_users"] = self.get_action("deactivate_users")
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            actions["deactivate_users"] = self.get_action("deactivate_users")


        return actions

    actions = [] 

    def has_delete_permission(self, request, obj=None):
        return False

    def has_import_permission(self, request):
        """
        Control import permission based on user role.
        """
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        elif request.user.group == UserGroup.LABORATORY_ASSISTANT.value:
            return True
        return False

    def has_export_permission(self, request):
        """Control export permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        return False

    def has_module_permission(self, request):
        """Control module access based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        return False

    def has_view_permission(self, request, obj=None):
        """Control view permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        return False

    def has_add_permission(self, request):
        """
        Control add permission based on user role.
        """
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """
        Control edit permission based on user role.
        """
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        return False

    def get_list_display_links(self, request, list_display):
        """
        Disable edit links for users without change permission.
        """
        if not self.has_change_permission(request):
            return None
        return super().get_list_display_links(request, list_display)

    # def process_import(self, request, *args, **kwargs):
    #     if not self._has_lab_employee_permission(request):
    #         messages.error(request, _("Only laboratory employees can import data"))
    #         return redirect(request.META.get("HTTP_REFERER", "admin:index"))
    #     return super().process_import(request, *args, **kwargs)
