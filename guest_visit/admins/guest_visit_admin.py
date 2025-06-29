"""
Django admin configuration for Guest Visit management.

Provides admin interface for guest visit management with conditional field display
based on visitor type (manual entry vs registered user) and soft delete functionality.
"""

from core.enums import VisitorIdentityType
from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportMixin
from shared.utils import (
    AuditFieldMixin,
    EnhancedExportAdminMixin,
    StandardExportFormatMixin,
    create_activate_action,
    create_deactivate_action,
)
from shared.utils.permission_config_utils import admin_laboratory_employee_only

from ..models import GuestVisitModel
from .guest_visit_resource import GuestVisitResource
from .views.guest_visit_export_view import GuestVisitExportView


class GuestVisitAdminForm(forms.ModelForm):
    """
    Custom guest visit admin form with conditional field validation.
    """

    class Meta:
        model = GuestVisitModel
        fields = "__all__"

    def clean(self):
        """Apply conditional validation logic similar to the model."""
        cleaned_data = super().clean()
        if cleaned_data is None:
            cleaned_data = {}

        visitor = cleaned_data.get("visitor")
        name = cleaned_data.get("name")
        identity_type = cleaned_data.get("identity_type")
        identity_number = cleaned_data.get("identity_number")

        # Use model's validation logic
        temp_instance = GuestVisitModel(**cleaned_data)
        try:
            temp_instance.clean()
        except Exception as e:
            raise forms.ValidationError(str(e))

        return cleaned_data


class GuestVisitAdmin(
    EnhancedExportAdminMixin,
    StandardExportFormatMixin,
    AuditFieldMixin,
    ExportMixin,
    admin.ModelAdmin,
):
    """Admin interface for Guest Visit management with enhanced export functionality."""

    form = GuestVisitAdminForm
    resource_class = GuestVisitResource

    # Enhanced export configuration
    export_view_class = GuestVisitExportView
    export_filtered_url_name = "guest_visit_guestvisitmodel_export_filtered"

    list_display = [
        "get_visitor_display",
        "date",
        "time_display",
        "purpose_short",
        "host_display",
    ]

    list_filter = [
        "date",
        "identity_type",
        "is_active",
        "created_at",
    ]

    search_fields = [
        "name",
        "visitor__first_name",
        "visitor__last_name",
        "visitor__username",
        "purpose",
        "identity_number",
    ]

    readonly_fields = (
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    ordering = ["-date", "-start_time"]
    date_hierarchy = "date"

    # Fieldsets for adding new guest visit (different from editing)
    add_fieldsets = (
        (
            _("Visitor Information"),
            {
                "fields": (
                    "visitor",
                    "name",
                    "identity_type",
                    "identity_number",
                ),
                "description": _(
                    "Select registered user OR fill manual entry fields (name is required for manual entry)"
                ),
            },
        ),
        (
            _("Visit Details"),
            {
                "fields": (
                    "date",
                    "start_time",
                    "end_time",
                    "purpose",
                    "paraf",
                ),
            },
        ),
    )

    # Fieldsets for editing existing guest visit
    fieldsets = (
        (
            _("Visitor Information"),
            {
                "fields": (
                    "visitor",
                    "name",
                    "identity_type",
                    "identity_number",
                ),
                "description": _(
                    "Select registered user OR fill manual entry fields (name is required for manual entry)"
                ),
            },
        ),
        (
            _("Visit Details"),
            {
                "fields": (
                    "date",
                    "start_time",
                    "end_time",
                    "purpose",
                    "paraf",
                    "staff",
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

    def get_visitor_display(self, obj):
        """Display visitor name from either manual entry or registered user."""
        return obj.get_visitor_name()

    get_visitor_display.short_description = _("Visitor")

    def purpose_short(self, obj):
        """Display shortened purpose."""
        if obj.purpose:
            return obj.purpose[:50] + "..." if len(obj.purpose) > 50 else obj.purpose
        return "-"

    purpose_short.short_description = _("Purpose")

    def time_display(self, obj):
        """Display formatted time range."""
        if obj.start_time and obj.end_time:
            return (
                f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
            )
        elif obj.start_time:
            return f"{obj.start_time.strftime('%H:%M')} - "
        return "-"

    time_display.short_description = _("Time")

    def host_display(self, obj):
        """Display host user name."""
        if obj.staff:
            return f"{obj.staff.first_name} {obj.staff.last_name}"
        return "-"

    host_display.short_description = _("Host")

    def get_fieldsets(self, request, obj=None):
        """Use different fieldsets for add vs change."""
        if obj is None:  # Adding new object
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_queryset(self, request):
        """
        Optimize queryset with select_related.

        For superuser, return all entries.
        For others, return only active entries.
        """
        qs = (
            super()
            .get_queryset(request)
            .select_related("visitor", "staff", "created_by", "updated_by")
        )

        if not getattr(request.user, "is_superuser", False):
            qs = qs.filter(is_active=True)

        return qs

    def save_model(self, request, obj, form, change):
        """Set created_by/updated_by and staff fields."""
        if not change:  # Creating new object
            obj.created_by = request.user
            # Auto set staff to the person creating the visit
            if not obj.staff:
                obj.staff = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    @admin_laboratory_employee_only
    def activate_guest_visits(self, request, queryset):
        """Restore selected guest visits - restricted to lab employees."""
        activate_action = create_activate_action(
            model_name="guest visit",
            superuser_only=False,
            verbose_name=_("Restore Selected Guest Visits"),
        )
        return activate_action(self, request, queryset)

    activate_guest_visits.short_description = _("Restore Selected Guest Visits")

    @admin_laboratory_employee_only
    def deactivate_guest_visits(self, request, queryset):
        """Delete selected guest visits - restricted to lab employees."""
        deactivate_action = create_deactivate_action(
            model_name="guest visit",
            superuser_only=False,
            verbose_name=_("Delete Selected Guest Visits"),
        )
        return deactivate_action(self, request, queryset)

    deactivate_guest_visits.short_description = _("Delete Selected Guest Visits")

    def get_actions(self, request):
        """Control actions - remove hard delete, keep soft delete."""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    actions = ["activate_guest_visits", "deactivate_guest_visits"]

    def has_delete_permission(self, request, obj=None):
        """Disable hard delete - use soft delete instead."""
        return False
