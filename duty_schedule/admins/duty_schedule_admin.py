"""
Django admin configuration for Duty Schedule management.

Provides streamlined admin interface for duty schedule management with
mandatory bulk generation capabilities for creating duty attendance records.

Role-based permissions:
- Superuser: view, add, change, delete/restore/regenerate actions, no export/import
- Kepala Laboratorium: view only, no actions, no export/import
- Teknisi: view, add, change, delete action, no export/import
- Asisten: no access
"""

from core.enums import UserGroup
from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from shared.utils import (
    AuditFieldMixin,
    create_activate_action,
    create_deactivate_action,
)
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
class DutyScheduleAdmin(AuditFieldMixin, admin.ModelAdmin):
    form = DutyScheduleAdminForm

    list_display = [
        "days",
        "time_display",
        "assistants_count",
        "generation_status",
    ]

    list_filter = [
        "start_date",
        "is_generated",
        "days",
        "is_active",
    ]

    search_fields = [
        "days",
        "laboratory_assistants__username",
        "laboratory_assistants__first_name",
        "laboratory_assistants__last_name",
    ]

    readonly_fields = (
        "is_generated",
        "generated_count",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    ordering = ["-start_date", "-start_time"]
    date_hierarchy = "start_date"

    add_fieldsets = (
        (
            _("New Duty Schedule"),
            {
                "fields": (
                    "start_date",
                    "end_date",
                    "days",
                    "laboratory_assistants",
                    "start_time",
                    "end_time",
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
                    "start_date",
                    "end_date",
                    "days",
                    "laboratory_assistants",
                    "start_time",
                    "end_time",
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

    filter_horizontal = ("laboratory_assistants",)

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

    def assistants_count(self, obj):
        """Display number of assigned assistants."""
        return obj.laboratory_assistants.count()

    assistants_count.short_description = _("Assistants")

    def generation_status(self, obj):
        """Display generation status with count."""
        if obj.is_generated:
            return f"✓ Generated ({obj.generated_count} records)"
        return "⏳ Not Generated"

    generation_status.short_description = _("Status")

    def get_queryset(self, request):
        qs = (
            super()
            .get_queryset(request)
            .select_related("created_by", "updated_by")
            .prefetch_related("laboratory_assistants")
        )

        if not getattr(request.user, "is_superuser", False):
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
        """Audit fields handled by AuditFieldMixin."""
        # Let AuditFieldMixin handle the audit fields
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        """Handle many-to-many relationships and automatic bulk generation."""
        # Save many-to-many relationships first
        super().save_related(request, form, formsets, change)

        obj = form.instance

        # Auto-generate attendance records for new duty schedules
        if not change and obj.end_date and obj.days:
            try:
                created = self._create_bulk_duty_schedules(request, obj)
                self.message_user(
                    request,
                    _(
                        "✅ Duty schedule created! Auto-generated {count} attendance records "
                        "for {assistants} assistants."
                    ).format(
                        count=created, assistants=obj.laboratory_assistants.count()
                    ),
                )
            except Exception as e:
                self.message_user(
                    request,
                    _("❌ Error generating attendance records: {error}").format(
                        error=str(e)
                    ),
                    level="error",
                )

        # Auto-generate attendance records for updated duty schedules (incremental)
        elif change and obj.end_date and obj.days:
            try:
                # Use incremental generation - only create missing records
                new_records, existing_count = obj.generate_missing_attendance_records(
                    commit=True
                )

                if new_records:
                    self.message_user(
                        request,
                        _(
                            "🔄 Duty schedule updated! Created {new_count} new attendance records. "
                            "{existing_count} existing records preserved for {assistants} assistants."
                        ).format(
                            new_count=len(new_records),
                            existing_count=existing_count,
                            assistants=obj.laboratory_assistants.count(),
                        ),
                    )
                elif existing_count > 0:
                    self.message_user(
                        request,
                        _(
                            "ℹ️ Duty schedule updated! All {existing_count} attendance records already exist - no new records needed."
                        ).format(existing_count=existing_count),
                    )
                else:
                    self.message_user(
                        request,
                        _(
                            "ℹ️ Duty schedule updated - no attendance records to generate."
                        ),
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
            raise PermissionDenied(message)

        # Clear existing records
        obj.clear_attendance_records()

        # Generate new records
        attendance_records = obj.generate_attendance_records(commit=True)

        return len(attendance_records)

    @admin_laboratory_employee_only
    def regenerate_attendance_records(self, request, queryset):
        """Regenerate attendance records for selected duty schedules - superuser only."""
        if not request.user.is_superuser:
            raise PermissionDenied(
                _("Only superusers can regenerate attendance records.")
            )

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
            except PermissionDenied as e:
                error_count += 1
                self.message_user(
                    request,
                    _("Error regenerating {title}: {error}").format(
                        title=obj.days, error=str(e)
                    ),
                    level="warning",
                )
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    _("Unexpected error for {title}: {error}").format(
                        title=obj.days, error=str(e)
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

    def activate_duty_schedules(self, request, queryset):
        """Restore selected duty schedules - superuser only."""
        if not request.user.is_superuser:
            raise PermissionDenied(_("Only superusers can restore duty schedules."))

        activate_action = create_activate_action(
            model_name="duty schedule",
            superuser_only=True,
            verbose_name=_("Restore Selected Duty Schedules"),
        )
        return activate_action(self, request, queryset)

    activate_duty_schedules.short_description = _("Restore Selected Duty Schedules")

    def deactivate_duty_schedules(self, request, queryset):
        """Delete selected duty schedules - superuser and teknisi only."""
        if not (
            request.user.is_superuser
            or request.user.group == UserGroup.LABORATORY_TECHNICIAN.value
        ):
            raise PermissionDenied(
                _("Only superusers and technicians can delete duty schedules.")
            )

        deactivate_action = create_deactivate_action(
            model_name="duty schedule",
            superuser_only=False,
            verbose_name=_("Delete Selected Duty Schedules"),
        )
        return deactivate_action(self, request, queryset)

    deactivate_duty_schedules.short_description = _("Delete Selected Duty Schedules")

    def get_actions(self, request):
        """
        Return actions based on user role.
        """
        actions = super().get_actions(request)

        if "delete_selected" in actions:
            del actions["delete_selected"]

        if request.user.is_superuser:
            actions["regenerate_attendance_records"] = self.get_action(
                "regenerate_attendance_records"
            )
            actions["activate_duty_schedules"] = self.get_action(
                "activate_duty_schedules"
            )
            actions["deactivate_duty_schedules"] = self.get_action(
                "deactivate_duty_schedules"
            )
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            actions["deactivate_duty_schedules"] = self.get_action(
                "deactivate_duty_schedules"
            )

        return actions

    actions = []  # Remove default actions, will be set by get_actions

    def has_delete_permission(self, request, obj=None):
        """No hard delete - only soft delete via actions."""
        return False

    def _create_missing_duty_schedules(self, request, obj):
        """
        Generate only missing DutyAttendanceModel records for the duty schedule.

        Uses incremental generation approach - only creates records that don't exist.
        """
        new_records, existing_count = obj.generate_missing_attendance_records(
            commit=True
        )
        return len(new_records), existing_count

    def has_module_permission(self, request):
        """Control module access based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_HEAD.value:
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
        """Control change permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """No hard delete - only soft delete via actions."""
        return False

    def has_export_permission(self, request):
        """No export permission for any role."""
        return False

    def has_import_permission(self, request):
        """No import permission for any role."""
        return False

    def get_list_display_links(self, request, list_display):
        """
        Disable edit links for users without change permission.
        """
        if not self.has_change_permission(request):
            return None
        return super().get_list_display_links(request, list_display)
