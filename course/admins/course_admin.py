"""
Django admin configuration for Course models.

This module provides admin interface for course and course session models
following the established patterns in the project.
"""

from core.enums import UserGroup
from core.enums.user_group_enum import UserGroup as UserGroupEnum
from django import forms
from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportMixin
from shared.utils import (
    AuditFieldMixin,
    create_activate_action,
    create_deactivate_action,
)
from shared.utils.permission_config_utils import (
    has_group_permission,
)

from ..models import CourseModel, CourseSessionModel
from .course_resource import CourseResource


class CourseSessionInline(admin.StackedInline):
    """Inline admin for course sessions - Moodle-like experience with vertical layout."""

    model = CourseSessionModel
    extra = 1

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "description",
                    "type",
                    "date",
                    "start_time",
                    "end_time",
                    "status",
                )
            },
        ),
        (
            _("Teaching Assistants"),
            {
                "fields": ("teaching_assistants",),
                "classes": ("wide",),
            },
        ),
    )

    filter_horizontal = ("teaching_assistants",)

    classes = ["collapse"]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Only show TAs assigned to parent course."""
        if db_field.name == "teaching_assistants":
            # Get course from URL parameter
            if (
                hasattr(request, "resolver_match")
                and request.resolver_match
                and hasattr(request.resolver_match, "kwargs")
                and request.resolver_match.kwargs
                and request.resolver_match.kwargs.get("object_id")
            ):
                course_id = request.resolver_match.kwargs["object_id"]
                try:
                    course = CourseModel.objects.get(pk=course_id)
                    kwargs["queryset"] = course.teaching_assistants.filter(
                        is_active=True
                    )
                except CourseModel.DoesNotExist:
                    from django.contrib.auth import get_user_model

                    User = get_user_model()
                    kwargs["queryset"] = User.objects.none()
            else:
                # For new courses, show all active lab assistants
                from django.contrib.auth import get_user_model

                User = get_user_model()
                kwargs["queryset"] = User.objects.filter(
                    is_active=True, groups__name=UserGroup.LABORATORY_ASSISTANT.value
                ).order_by("first_name", "last_name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_queryset(self, request):
        """Only show active sessions."""
        return super().get_queryset(request).filter(is_active=True)


class CourseAdminForm(forms.ModelForm):
    """Custom course admin form with validation."""

    class Meta:
        model = CourseModel
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data is None:
            cleaned_data = {}
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError(_("End date must be after start date."))

        return cleaned_data


@admin.register(CourseModel)
class CourseAdmin(AuditFieldMixin, ExportMixin, admin.ModelAdmin):
    resource_class = CourseResource
    form = CourseAdminForm

    # Add filter_horizontal for better UX with many-to-many fields
    filter_horizontal = ("teaching_assistants", "students")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Customize queryset for many-to-many fields."""
        if db_field.name == "teaching_assistants":
            # Only show Laboratory Assistants
            from django.contrib.auth import get_user_model

            User = get_user_model()
            kwargs["queryset"] = User.objects.filter(
                is_active=True, groups__name=UserGroup.LABORATORY_ASSISTANT.value
            ).order_by("first_name", "last_name")
        elif db_field.name == "students":
            # Only show users from student groups (Laboratory Assistant + Student)
            from django.contrib.auth import get_user_model

            User = get_user_model()
            kwargs["queryset"] = User.objects.filter(
                is_active=True, groups__name__in=UserGroup.student_groups()
            ).order_by("first_name", "last_name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_inlines(self, request, obj):
        """Only show sessions inline when editing existing course, not when creating new course."""
        if obj:
            return [CourseSessionInline]
        else:
            return []

    list_display = [
        "title",
        "start_date",
        "end_date",
        "total_sessions",
    ]

    list_filter = [
        "start_date",
        "end_date",
    ]

    search_fields = [
        "title",
        "description",
        "students__first_name",
        "students__last_name",
        "teaching_assistants__first_name",
        "teaching_assistants__last_name",
    ]

    readonly_fields = [
        "total_sessions",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    ]

    def get_fieldsets(self, request, obj=None):
        """Different fieldsets for add vs change views."""

        add_fieldsets = (
            (
                _("Course Information"),
                {
                    "fields": (
                        "title",
                        "description",
                        "start_date",
                        "end_date",
                        "enroll_key",
                        "image",
                    )
                },
            ),
            (
                _("Participants"),
                {
                    "fields": (
                        "teaching_assistants",
                        "students",
                    ),
                    "classes": ("wide",),
                },
            ),
        )

        fieldsets = (
            (
                _("Course Information"),
                {
                    "fields": (
                        "title",
                        "description",
                        "start_date",
                        "end_date",
                        "enroll_key",
                        "image",
                    )
                },
            ),
            (
                _("Participants"),
                {
                    "fields": (
                        "teaching_assistants",
                        "students",
                    ),
                    "classes": ("wide",),
                },
            ),
            (
                _("Statistics"),
                {
                    "fields": ("total_sessions",),
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

        if obj:  # Editing existing course
            return fieldsets
        else:  # Creating new course
            return add_fieldsets


    ordering = ["-start_date", "title"]
    date_hierarchy = "start_date"

    def save_model(self, request, obj, form, change):
        """Audit fields handled by AuditFieldMixin."""
        super().save_model(request, obj, form, change)

    @admin.display(description=_("Total Sessions"))
    def total_sessions(self, obj):
        """Display total number of sessions."""
        return obj.sessions.filter(is_active=True).count()

    def get_queryset(self, request):
        """Optimize queryset with prefetch_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related("created_by", "updated_by").prefetch_related(
            "students", "teaching_assistants", "sessions"
        )

    def changelist_view(self, request, extra_context=None):
        """Override changelist view with permission check."""
        if not getattr(request.user, "is_superuser", False):
            if not has_group_permission(
                request.user, [UserGroupEnum.LABORATORY_ASSISTANT]
            ):
                from django.contrib import messages

                messages.error(
                    request,
                    _("Only laboratory employees can perform this admin action"),
                )
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
        return super().changelist_view(request, extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        """Override add view with permission check."""
        if not getattr(request.user, "is_superuser", False):
            if not has_group_permission(
                request.user, [UserGroupEnum.LABORATORY_ASSISTANT]
            ):
                from django.contrib import messages

                messages.error(
                    request,
                    _("Only laboratory employees can perform this admin action"),
                )
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Override change view with permission check."""
        if not getattr(request.user, "is_superuser", False):
            if not has_group_permission(
                request.user, [UserGroupEnum.LABORATORY_ASSISTANT]
            ):
                from django.contrib import messages

                messages.error(
                    request,
                    _("Only laboratory employees can perform this admin action"),
                )
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
        return super().change_view(request, object_id, form_url, extra_context)

    def get_import_formats(self):
        """Disable import - this is export-only."""
        return []

    def has_import_permission(self, request):
        """Disable import - this is export-only."""
        return False

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

    def activate_courses(self, request, queryset):
        if not getattr(request.user, 'is_superuser', False):
            if not has_group_permission(request.user, [UserGroup.LABORATORY_ASSISTANT]):
                from django.contrib import messages
                messages.error(request, _("Only laboratory employees can perform this admin action"))
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
        
        updated = 0
        for course in queryset:
            if not course.is_active:
                course.is_active = True
                course.save()
                updated += 1

        if updated:
            self.message_user(
                request, _("{} course(s) were successfully restored.").format(updated)
            )
        else:
            self.message_user(request, _("No courses needed to be restored."))

    activate_courses.short_description = _("Restore Selected Courses")

    def deactivate_courses(self, request, queryset):
        """Delete selected courses - restricted to lab employees."""
        if not getattr(request.user, 'is_superuser', False):
            if not has_group_permission(request.user, [UserGroup.LABORATORY_ASSISTANT]):
                from django.contrib import messages
                messages.error(request, _("Only laboratory employees can perform this admin action"))
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
        
        updated = 0
        for course in queryset:
            if course.is_active:
                course.is_active = False
                course.save()
                updated += 1

        if updated:
            self.message_user(
                request, _("{} session(s) were successfully deleted.").format(updated)
            )
        else:
            self.message_user(request, _("No courses needed to be deleted."))

    deactivate_courses.short_description = _("Delete Selected Courses")

    def get_actions(self, request):
        """
        Return actions based on user role.
        """
        actions = super().get_actions(request)

        if request.user.is_superuser:
            actions["activate_courses"] = self.get_action("activate_courses")
            actions["deactivate_courses"] = self.get_action("deactivate_courses")
        # elif request.user.group == UserGroup.LABORATORY_ASSISTANT.value:
        #     actions["deactivate_courses"] = self.get_action("deactivate_courses")

        return actions
