"""
Django admin configuration for Course Session model.

This module provides admin interface for course session management
following the established patterns in the project.
"""

from core.enums.user_group_enum import UserGroup
from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportMixin
from shared.utils import (
    AuditFieldMixin,
    ExportOnlyMixin,
    LabEmployeePermissionMixin,
    StandardExportFormatMixin,
)
from shared.utils.permission_config_utils import (
    admin_laboratory_employee_only,
    has_group_permission,
)

from ..models import CourseSessionModel
from .course_resource import CourseSessionResource


class CourseSessionAdminForm(forms.ModelForm):
    """Custom course session admin form with validation."""

    class Meta:
        model = CourseSessionModel
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data is None:
            cleaned_data = {}

        # Check if editing an existing session that has already passed
        if self.instance and self.instance.pk and self.instance.date:
            from django.utils import timezone

            current_datetime = timezone.localtime()
            current_date = current_datetime.date()
            current_time = current_datetime.time()

            # If session date has passed completely
            if self.instance.date < current_date:
                raise forms.ValidationError(
                    _(
                        "Cannot edit session that has already passed. Session date: {}"
                    ).format(self.instance.date)
                )

            # If session is today and time has passed
            elif (
                self.instance.date == current_date
                and self.instance.end_time
                and self.instance.end_time < current_time
            ):
                raise forms.ValidationError(
                    _(
                        "Cannot edit session that has already ended. Session ended at: {}"
                    ).format(self.instance.end_time.strftime("%H:%M"))
                )

        # Validate time range
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(_("Session end time must be after start time."))

        # Validate session date is within course date range
        course = cleaned_data.get("course")
        date = cleaned_data.get("date")

        if course and date and course.start_date and course.end_date:
            if date < course.start_date or date > course.end_date:
                raise forms.ValidationError(
                    _(
                        "Session date must be within course date range ({} - {})."
                    ).format(course.start_date, course.end_date)
                )

        return cleaned_data


@admin.register(CourseSessionModel)
class CourseSessionAdmin(
    LabEmployeePermissionMixin,
    StandardExportFormatMixin,
    ExportOnlyMixin,
    AuditFieldMixin,
    ExportMixin,
    admin.ModelAdmin,
):
    """Admin interface for Course Session management."""

    resource_class = CourseSessionResource
    form = CourseSessionAdminForm

    list_display = [
        "title",
        "course",
        "date",
        "time_display",
        "status",
        "teaching_assistants_display",
    ]

    list_filter = [
        "status",
        "date",
        "course",
    ]

    search_fields = [
        "title",
        "description",
        "course__title",
        "teaching_assistants__first_name",
        "teaching_assistants__last_name",
    ]

    readonly_fields = (
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    filter_horizontal = ("teaching_assistants",)
    ordering = ["-date", "-start_time"]
    date_hierarchy = "date"

    add_fieldsets = (
        (
            _("Session Information"),
            {
                "fields": (
                    "course",
                    "title",
                    "description",
                    "type",
                    "date",
                    "start_time",
                    "end_time",
                    "status",
                ),
                "description": _("Basic session information and scheduling."),
            },
        ),
        (
            _("Teaching Assistants"),
            {
                "fields": ("teaching_assistants",),
                "description": _("Assign teaching assistants to this session."),
            },
        ),
    )

    fieldsets = (
        (
            _("Session Information"),
            {
                "fields": (
                    "course",
                    "title",
                    "description",
                    "type",
                    "date",
                    "start_time",
                    "end_time",
                    "status",
                ),
                "description": _("Basic session information and scheduling."),
            },
        ),
        (
            _("Teaching Assistants"),
            {
                "fields": ("teaching_assistants",),
                "description": _("Assign teaching assistants to this session."),
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

    def get_fieldsets(self, request, obj=None):
        """Use different fieldsets for add vs change."""
        if obj is None:  # Adding new object
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_queryset(self, request):
        qs = (
            super()
            .get_queryset(request)
            .select_related("course", "created_by", "updated_by")
            .prefetch_related("teaching_assistants")
        )

        if not getattr(request.user, "is_superuser", False):
            qs = qs.filter(is_active=True)

        return qs

    def time_display(self, obj):
        """Display formatted time range."""
        if obj.start_time and obj.end_time:
            return (
                f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
            )
        return "-"

    time_display.short_description = _("Time")

    def teaching_assistants_display(self, obj):
        """Display teaching assistants names."""
        tas = obj.teaching_assistants.all()
        if tas:
            return ", ".join([f"{ta.first_name} {ta.last_name}" for ta in tas])
        return "-"

    teaching_assistants_display.short_description = _("Teaching Assistants")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize ForeignKey fields."""
        if db_field.name == "course":
            from ..models import CourseModel

            kwargs["queryset"] = CourseModel.objects.filter(is_active=True).order_by(
                "title"
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Customize ManyToMany field querysets."""
        if db_field.name == "teaching_assistants":
            from django.contrib.auth import get_user_model

            User = get_user_model()
            kwargs["queryset"] = User.objects.filter(is_active=True).order_by(
                "first_name", "last_name"
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def activate_sessions(self, request, queryset):
        """Restore selected course sessions - restricted to lab employees."""
        if not getattr(request.user, 'is_superuser', False):
            if not has_group_permission(request.user, [UserGroup.LABORATORY_ASSISTANT]):
                from django.contrib import messages
                messages.error(request, _("Only laboratory employees can perform this admin action"))
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
        
        updated = 0
        for session in queryset:
            if not session.is_active:
                session.is_active = True
                session.save()
                updated += 1

        if updated:
            self.message_user(
                request, _("{} session(s) were successfully restored.").format(updated)
            )
        else:
            self.message_user(request, _("No sessions needed to be restored."))

    activate_sessions.short_description = _("Restore Selected Sessions")

    def deactivate_sessions(self, request, queryset):
        """Delete selected course sessions - restricted to lab employees."""
        if not getattr(request.user, 'is_superuser', False):
            if not has_group_permission(request.user, [UserGroup.LABORATORY_ASSISTANT]):
                from django.contrib import messages
                messages.error(request, _("Only laboratory employees can perform this admin action"))
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
        
        updated = 0
        for session in queryset:
            if session.is_active:
                session.is_active = False
                session.save()
                updated += 1

        if updated:
            self.message_user(
                request, _("{} session(s) were successfully deleted.").format(updated)
            )
        else:
            self.message_user(request, _("No sessions needed to be deleted."))

    deactivate_sessions.short_description = _("Delete Selected Sessions")

    def has_delete_permission(self, request, obj=None):
        """Disable hard delete - use soft delete instead."""
        return False

    def has_module_permission(self, request):
        """Control module access based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_ASSISTANT.value:
            return True
        return False

    def has_view_permission(self, request, obj=None):
        """Control view permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_ASSISTANT.value:
            return True
        return False

    def has_add_permission(self, request):
        """Control add permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_ASSISTANT.value:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """Control change permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_ASSISTANT.value:
            return True
        return False

    def has_export_permission(self, request):
        """Control export permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_ASSISTANT.value:
            return True
        return False

    def get_actions(self, request):
        """
        Return actions based on user role.
        """
        actions = super().get_actions(request)

        if request.user.is_superuser:
            actions["activate_sessions"] = self.get_action("activate_sessions")
            actions["deactivate_sessions"] = self.get_action("deactivate_sessions")
        # elif request.user.group == UserGroup.LABORATORY_ASSISTANT.value:
        #     actions["deactivate_sessions"] = self.get_action("deactivate_sessions")


        return actions

    actions = [] 
