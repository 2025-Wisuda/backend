"""
Simple Course Session Attendance Admin Interface.

Key Features:
- Simple list view (read-only)
- Edit only attendance status
- Auto-generate marked_at and marked_by
- No add/delete functionality
"""

from core.enums.user_group_enum import UserGroup
from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportMixin
from shared.utils import AuditFieldMixin, StandardExportFormatMixin
from shared.utils.permission_config_utils import has_group_permission

from ..models import CourseSessionAttendanceModel
from .course_session_attendance_resource import CourseSessionAttendanceResource
from .views.course_session_attendance_export_view import (
    CourseSessionAttendanceExportView,
)


@admin.register(CourseSessionAttendanceModel)
class CourseSessionAttendanceAdmin(
    StandardExportFormatMixin,
    AuditFieldMixin,
    ExportMixin,
    admin.ModelAdmin,
):
    """
    Enhanced admin interface for Course Session Attendance with export functionality.

    - List view: Simple display of attendance records
    - Edit: Only attendance status
    - Auto-generate: marked_at and marked_by from request user
    - No add/delete functionality
    - Export: Custom export with course and session filtering
    """

    resource_class = CourseSessionAttendanceResource

    export_view_class = CourseSessionAttendanceExportView
    export_filtered_url_name = "course_coursesessionattendancemodel_export_filtered"

    def get_urls(self):
        """Add custom export URL."""
        from django.urls import path

        urls = super().get_urls()

        if self.export_view_class:
            custom_urls = [
                path(
                    "export-filtered/",
                    self.admin_site.admin_view(
                        self.export_view_class(self).export_action
                    ),
                    name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_export_filtered",
                ),
            ]
            return custom_urls + urls
        return urls

    def export_with_filters(self, request, queryset=None):
        """Manual export with permission check."""
        if not getattr(request.user, "is_superuser", False):
            if not has_group_permission(request.user, [UserGroup.LABORATORY_ASSISTANT]):
                from django.contrib import messages

                messages.error(request, _("Only laboratory employees can export data"))
                from django.shortcuts import redirect

                return redirect(request.META.get("HTTP_REFERER", "admin:index"))

        if self.export_filtered_url_name:
            from django.urls import reverse

            return redirect(reverse(f"admin:{self.export_filtered_url_name}"))

        # Fallback to standard export
        return super().export_action(request, queryset)

    list_display = [
        "student",
        "course_session",
        "status",
        "marked_at",
        "marked_by",
    ]

    list_filter = [
        "status",
        "course_session__course",
        "course_session__date",
        "marked_at",
    ]

    search_fields = [
        "student__first_name",
        "student__last_name",
        "student__student_number",
        "course_session__title",
    ]

    fields = [
        "course_session",
        "student",
        "status",
        "marked_at",
        "marked_by",
    ]

    readonly_fields = [
        "course_session",
        "student",
        "marked_at",
        "marked_by",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            obj.marked_at = timezone.localtime()
            obj.marked_by = request.user
        super().save_model(request, obj, form, change)

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

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "student", "course_session", "course_session__course", "marked_by"
            )
        )
