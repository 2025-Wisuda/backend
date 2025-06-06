"""
Django admin configuration for Lab Allocation management.

Provides streamlined admin interface for technician-managed lab allocations
with auto-approval and bulk generation capabilities.
"""

from datetime import timedelta

from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.enums import BulkDays
from shared.utils import create_activate_action, create_deactivate_action
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
        """Validate that allocation_days is required when allocation_end_date is provided."""
        cleaned_data = super().clean()
        allocation_end_date = cleaned_data.get("allocation_end_date")
        allocation_days = cleaned_data.get("allocation_days")

        if allocation_end_date and not allocation_days:
            raise forms.ValidationError(
                _(
                    "Allocation days must be selected when creating bulk allocations with an end date."
                )
            )

        if allocation_days and not allocation_end_date:
            raise forms.ValidationError(
                _(
                    "End date must be provided when allocation days are selected for bulk generation."
                )
            )

        return cleaned_data


@admin.register(LabAllocationModel)
class LabAllocationAdmin(admin.ModelAdmin):
    form = LabAllocationAdminForm

    list_display = [
        "allocation_type",
        "allocation_start_date",
        "time_display",
        "allocation_details_short",
    ]

    list_filter = [
        "allocation_type",
        "allocation_start_date",
    ]

    search_fields = [
        "allocation_details",
    ]

    readonly_fields = (
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    ordering = ["-allocation_start_date", "-allocation_start_time"]
    date_hierarchy = "allocation_start_date"

    add_fieldsets = (
        (
            _("New Lab Allocation"),
            {
                "fields": (
                    "allocation_type",
                    "allocation_details",
                    "allocation_start_date",
                    "allocation_start_time",
                    "allocation_end_time",
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
                    "allocation_end_date",
                    "allocation_days",
                ),
                "description": _(
                    "Fill allocation_end_date and select days to create multiple allocations at once."
                ),
            },
        ),
    )

    fieldsets = (
        (
            _("Allocation Information"),
            {
                "fields": (
                    "allocation_type",
                    "allocation_details",
                    "allocation_start_date",
                    "allocation_start_time",
                    "allocation_end_time",
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

    def allocation_details_short(self, obj):
        """Display shortened allocation details."""
        if obj.allocation_details:
            return (
                obj.allocation_details[:50] + "..."
                if len(obj.allocation_details) > 50
                else obj.allocation_details
            )
        return "-"

    allocation_details_short.short_description = _("Details")

    def time_display(self, obj):
        """Display formatted time range."""
        if obj.allocation_start_time and obj.allocation_end_time:
            return f"{obj.allocation_start_time.strftime('%H:%M')} - {obj.allocation_end_time.strftime('%H:%M')}"
        elif obj.allocation_start_time:
            return f"{obj.allocation_start_time.strftime('%H:%M')} - "
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

        start_date = obj.allocation_start_date
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
                    allocation_type=obj.allocation_type,
                    allocation_details=obj.allocation_details,
                    allocation_start_date=current_date,
                    allocation_start_time=obj.allocation_start_time,
                    allocation_end_time=obj.allocation_end_time,
                    created_by=request.user,
                    updated_by=request.user,
                )
                created += 1
            current_date += timedelta(days=1)

        return created

    def save_model(self, request, obj, form, change):
        """Set created_by/updated_by and handle bulk generation."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user

        bulk_end_date = form.cleaned_data.get("allocation_end_date")
        bulk_days = form.cleaned_data.get("allocation_days", "")
        is_bulk = not change and bulk_end_date and bulk_days

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
        """Control actions - remove hard delete, keep soft delete."""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    actions = ["activate_allocations", "deactivate_allocations"]

    def has_delete_permission(self, request, obj=None):
        """No hard delete - only soft delete via actions."""
        return False
