"""
Django admin configuration for Lab Allocation management.

Provides streamlined admin interface for technician-managed lab allocations
with auto-approval and bulk generation capabilities.
"""

from datetime import timedelta

from core.enums import BulkDays, UserGroup
from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from shared.utils import (
    AuditFieldMixin,
    create_activate_action,
    create_deactivate_action,
)
from shared.utils.permission_config_utils import admin_laboratory_employee_only

from ..models import LabAllocationModel


class LabAllocationAdminForm(forms.ModelForm):
    """
    Custom lab allocation admin form with bulk generation support.
    """

    class Meta:
        model = LabAllocationModel
        fields = "__all__"

    def clean(self):
        """Validate that days is required when end_date is provided."""
        cleaned_data = super().clean()
        end_date = cleaned_data.get("end_date")
        days = cleaned_data.get("days")

        if end_date and not days:
            raise forms.ValidationError(
                _(
                    "Allocation days must be selected when creating bulk allocations with an end date."
                )
            )

        if days and not end_date:
            raise forms.ValidationError(
                _(
                    "End date must be provided when allocation days are selected for bulk generation."
                )
            )

        return cleaned_data


@admin.register(LabAllocationModel)
class LabAllocationAdmin(AuditFieldMixin, admin.ModelAdmin):
    form = LabAllocationAdminForm

    list_display = [
        "type",
        "start_date",
        "time_display",
        "detail_short",
    ]

    list_filter = [
        "type",
        "start_date",
    ]

    search_fields = [
        "detail",
    ]

    readonly_fields = (
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    ordering = ["-start_date", "-start_time"]
    date_hierarchy = "start_date"

    add_fieldsets = (
        (
            _("New Lab Allocation"),
            {
                "fields": (
                    "type",
                    "detail",
                    "start_date",
                    "start_time",
                    "end_time",
                ),
                "description": _(
                    "Please fill all field at this section for creating schedule."
                ),
            },
        ),
        (
            _("Bulk Generation (Optional)"),
            {
                "classes": ("collapse"),
                "fields": (
                    "end_date",
                    "days",
                ),
                "description": _(
                    "Fill end_date and select days to create multiple allocations at once."
                ),
            },
        ),
    )

    fieldsets = (
        (
            _("Allocation Information"),
            {
                "fields": (
                    "type",
                    "detail",
                    "start_date",
                    "start_time",
                    "end_time",
                )
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

    def detail_short(self, obj):
        """Display shortened allocation details."""
        if obj.detail:
            return obj.detail[:50] + "..." if len(obj.detail) > 50 else obj.detail
        return "-"

    detail_short.short_description = _("Details")

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

    def get_queryset(self, request):
        """
        Optimize queryset with select_related.

        For superuser, return all entries.
        For others, return only active entries.
        """
        qs = super().get_queryset(request).select_related("created_by", "updated_by")

        if not request.user.is_superuser:
            qs = qs.filter(is_active=True)

        return qs

    def get_fieldsets(self, request, obj=None):
        """Use different fieldsets for add vs change."""
        if obj is None:  # Adding new object
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def _create_bulk_allocations(self, request, obj, bulk_end_date, bulk_days):
        """Create multiple LabAllocationModel objects for bulk generation."""
        if hasattr(obj, "get_bulk_days_list"):
            day_names = obj.get_bulk_days_list()
        else:
            day_names = [
                day.strip() for day in (bulk_days or "").split(",") if day.strip()
            ]

        valid_days = set(
            [
                (
                    BulkDays[day.upper()].value
                    if day.upper() in BulkDays.__members__
                    else day
                )
                for day in day_names
            ]
        )
        weekday_enum = [
            BulkDays.MONDAY.value,
            BulkDays.TUESDAY.value,
            BulkDays.WEDNESDAY.value,
            BulkDays.THURSDAY.value,
            BulkDays.FRIDAY.value,
            BulkDays.SATURDAY.value,
            BulkDays.SUNDAY.value,
        ]

        start_date = obj.start_date
        end_date = bulk_end_date

        if not start_date or not end_date or not valid_days:
            return 0

        current_date = start_date
        created = 0

        while current_date <= end_date:
            if (
                current_date != start_date
                and weekday_enum[current_date.weekday()] in valid_days
            ):
                LabAllocationModel.objects.create(
                    type=obj.type,
                    detail=obj.detail,
                    start_date=current_date,
                    start_time=obj.start_time,
                    end_time=obj.end_time,
                    created_by=request.user,
                    updated_by=request.user,
                )
                created += 1
            current_date += timedelta(days=1)

        return created

    def save_model(self, request, obj, form, change):
        """Handle bulk generation - audit fields handled by AuditFieldMixin."""
        bulk_end_date = form.cleaned_data.get("end_date")
        bulk_days = form.cleaned_data.get("days", "")
        is_bulk = not change and bulk_end_date and bulk_days

        # Let AuditFieldMixin handle the audit fields
        super().save_model(request, obj, form, change)

        if is_bulk:
            created = self._create_bulk_allocations(
                request, obj, bulk_end_date, bulk_days
            )
            self.message_user(
                request,
                _(f"{created + 1} allocations created in bulk (including main entry)."),
            )

    @admin_laboratory_employee_only
    def activate_allocations(self, request, queryset):
        """Restore selected allocations - restricted to lab employees."""
        activate_action = create_activate_action(
            model_name="allocation",
            superuser_only=False,
            verbose_name=_("Restore Selected Allocations"),
        )
        return activate_action(self, request, queryset)

    activate_allocations.short_description = _("Restore Selected Allocations")

    @admin_laboratory_employee_only
    def deactivate_allocations(self, request, queryset):
        """Delete selected allocations - restricted to lab employees."""
        deactivate_action = create_deactivate_action(
            model_name="allocation",
            superuser_only=False,
            verbose_name=_("Delete Selected Allocations"),
        )
        return deactivate_action(self, request, queryset)

    deactivate_allocations.short_description = _("Delete Selected Allocations")

    def get_actions(self, request):
        """
        Control actions based on user role.
        """
        actions = super().get_actions(request)

        # Remove hard delete action
        if "delete_selected" in actions:
            del actions["delete_selected"]

        # Control soft delete/restore actions based on role
        if request.user.is_superuser:
            # Superuser: delete & restore
            actions["activate_allocations"] = self.get_action("activate_allocations")
            actions["deactivate_allocations"] = self.get_action(
                "deactivate_allocations"
            )
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            # Teknisi: delete only
            actions["deactivate_allocations"] = self.get_action(
                "deactivate_allocations"
            )
        # Kepala & Asisten: no actions

        return actions

    actions = []  # Remove default actions, will be set by get_actions

    def has_delete_permission(self, request, obj=None):
        """No hard delete - only soft delete via actions."""
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
        """Control add permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """Control edit permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        return False

    def has_import_permission(self, request):
        """Control import permission based on user role."""
        return False  # No import for anyone

    def has_export_permission(self, request):
        """Control export permission based on user role."""
        return False  # No export for anyone
