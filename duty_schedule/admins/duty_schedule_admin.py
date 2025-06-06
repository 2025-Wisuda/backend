"""
Django admin configuration for Duty Schedule management.

Provides streamlined admin interface for duty schedule management with 
mandatory bulk generation capabilities for creating duty attendance records.
"""

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from shared.utils import create_activate_action, create_deactivate_action
from shared.utils.permission_config_utils import admin_laboratory_employee_only

from ..models import DutyScheduleModel


class DutyScheduleAdminForm(forms.ModelForm):
    """
    Custom duty schedule admin form with mandatory bulk generation support.
    """

    class Meta:
        model = DutyScheduleModel
        fields = "__all__"


@admin.register(DutyScheduleModel)
class DutyScheduleAdmin(admin.ModelAdmin):
    form = DutyScheduleAdminForm

    list_display = [
        "duty_days",
        "time_display",
        "assistants_count",
        "generation_status",
    ]

    list_filter = [
        "duty_start_date",
        "is_generated",
        "duty_days",
    ]

    search_fields = [
        "duty_days",
        "duty_assistants__username",
        "duty_assistants__first_name",
        "duty_assistants__last_name",
    ]

    readonly_fields = (
        "is_generated",
        "generated_count",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    ordering = ["-duty_start_date", "-duty_start_time"]
    date_hierarchy = "duty_start_date"

    add_fieldsets = (
        (
            _("New Duty Schedule"),
            {
                "fields": (
                    "duty_start_date",
                    "duty_end_date",
                    "duty_days",
                    "duty_assistants",
                    "duty_start_time",
                    "duty_end_time",
                ),
                "description": _(
                    "Please fill all fields in this section for creating duty schedule."
                ),
            },
        ),
    )

    fieldsets = (
        (
            _("Duty Schedule Information"),
            {
                "fields": (
                    "duty_start_date",
                    "duty_end_date",
                    "duty_days",
                    "duty_assistants",
                    "duty_start_time",
                    "duty_end_time",
                )
            },
        ),
        (
            _("Generation Status"),
            {
                "fields": (
                    "is_generated",
                    "generated_count",
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

    filter_horizontal = ("duty_assistants",)

    def time_display(self, obj):
        """Display formatted time range."""
        if obj.duty_start_time and obj.duty_end_time:
            return f"{obj.duty_start_time.strftime('%H:%M')} - {obj.duty_end_time.strftime('%H:%M')}"
        elif obj.duty_start_time:
            return f"{obj.duty_start_time.strftime('%H:%M')} - "
        return "-"

    time_display.short_description = _("Time")

    def assistants_count(self, obj):
        """Display number of assigned assistants."""
        return obj.duty_assistants.count()

    assistants_count.short_description = _("Assistants")

    def generation_status(self, obj):
        """Display generation status with count."""
        if obj.is_generated:
            return f"✓ Generated ({obj.generated_count} records)"
        return "⏳ Not Generated"

    generation_status.short_description = _("Status")

    def get_queryset(self, request):
        """
        Optimize queryset with select_related and prefetch_related.

        For superuser, return all entries.
        For others, return only active entries.
        """
        qs = (
            super()
            .get_queryset(request)
            .select_related("created_by", "updated_by")
            .prefetch_related("duty_assistants")
        )

        if not request.user.is_superuser:
            qs = qs.filter(is_active=True)

        return qs

    def get_fieldsets(self, request, obj=None):
        """Use different fieldsets for add vs change."""
        if obj is None:  # Adding new object
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def _create_bulk_duty_schedules(self, request, obj):
        """
        Generate individual DutyAttendanceModel records for the duty schedule.

        Simple wrapper around the model's generate_attendance_records method.
        """
        attendance_records = obj.generate_attendance_records(commit=True)
        return len(attendance_records)

    def save_model(self, request, obj, form, change):
        """Set created_by/updated_by."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user

        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        """Handle many-to-many relationships and automatic bulk generation."""
        # Save many-to-many relationships first
        super().save_related(request, form, formsets, change)

        obj = form.instance

        # Auto-generate attendance records for new duty schedules
        if not change and obj.duty_end_date and obj.duty_days:
            try:
                created = self._create_bulk_duty_schedules(request, obj)
                self.message_user(
                    request,
                    _(
                        "✅ Duty schedule created! Auto-generated {count} attendance records "
                        "for {assistants} assistants."
                    ).format(count=created, assistants=obj.duty_assistants.count()),
                )
            except Exception as e:
                self.message_user(
                    request,
                    _("❌ Error generating attendance records: {error}").format(
                        error=str(e)
                    ),
                    level="error",
                )

    def _regenerate_attendance_records(self, request, obj):
        """
        Regenerate attendance records for a duty schedule.

        This will clear existing records and create new ones.
        Only allowed if no attendance has been completed.
        """
        can_regenerate, message = obj.can_regenerate()

        if not can_regenerate:
            raise ValidationError(message)

        # Clear existing records
        obj.clear_attendance_records()

        # Generate new records
        attendance_records = obj.generate_attendance_records(commit=True)

        return len(attendance_records)

    @admin_laboratory_employee_only
    def regenerate_attendance_records(self, request, queryset):
        """Regenerate attendance records for selected duty schedules."""
        if queryset.count() > 10:
            self.message_user(
                request,
                _(
                    "Cannot regenerate more than 10 schedules at once for performance reasons."
                ),
                level="error",
            )
            return

        regenerated_count = 0
        error_count = 0

        for obj in queryset:
            try:
                records_count = self._regenerate_attendance_records(request, obj)
                regenerated_count += records_count
            except ValidationError as e:
                error_count += 1
                self.message_user(
                    request,
                    _("Error regenerating {title}: {error}").format(
                        title=obj.duty_days, error=str(e)
                    ),
                    level="warning",
                )
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    _("Unexpected error for {title}: {error}").format(
                        title=obj.duty_days, error=str(e)
                    ),
                    level="error",
                )

        if regenerated_count > 0:
            self.message_user(
                request,
                _("Successfully regenerated {count} attendance records.").format(
                    count=regenerated_count
                ),
            )

    regenerate_attendance_records.short_description = _(
        "Regenerate Attendance Records (clears existing)"
    )

    @admin_laboratory_employee_only
    def activate_duty_schedules(self, request, queryset):
        """Restore selected duty schedules - restricted to lab employees."""
        activate_action = create_activate_action(
            model_name="duty schedule",
            superuser_only=False,
            verbose_name=_("Restore Selected Duty Schedules"),
        )
        return activate_action(self, request, queryset)

    activate_duty_schedules.short_description = _("Restore Selected Duty Schedules")

    @admin_laboratory_employee_only
    def deactivate_duty_schedules(self, request, queryset):
        """Delete selected duty schedules - restricted to lab employees."""
        deactivate_action = create_deactivate_action(
            model_name="duty schedule",
            superuser_only=False,
            verbose_name=_("Delete Selected Duty Schedules"),
        )
        return deactivate_action(self, request, queryset)

    deactivate_duty_schedules.short_description = _("Delete Selected Duty Schedules")

    def get_actions(self, request):
        """Control actions - remove hard delete, keep soft delete."""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    actions = [
        "regenerate_attendance_records",
        "activate_duty_schedules",
        "deactivate_duty_schedules",
    ]

    def has_delete_permission(self, request, obj=None):
        """No hard delete - only soft delete via actions."""
        return False
