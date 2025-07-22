"""
Course Session Attendance Export View for Django admin.

Provides custom export functionality for course session attendance data with comprehensive
filtering options and security controls.
"""

from datetime import datetime
from typing import Any, Dict

from core.enums.user_group_enum import UserGroup
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _
from shared.export import BaseExportView
from shared.utils.permission_config_utils import has_group_permission

from ...models import CourseModel, CourseSessionAttendanceModel, CourseSessionModel
from ..course_session_attendance_resource import CourseSessionAttendanceResource
from ..forms.course_session_attendance_export_form import (
    CourseSessionAttendanceExportForm,
)


class CourseSessionAttendanceExportView(BaseExportView):
    """
    Course Session Attendance export view with filtering and field selection.

    Features:
    - Course filtering
    - Course session filtering
    - Date range filtering
    - Attendance status filtering
    - Field selection
    - Permission controls (lab employees only)
    - Security: no sensitive data exposure
    """

    model = CourseSessionAttendanceModel
    resource_class = CourseSessionAttendanceResource
    form_class = CourseSessionAttendanceExportForm
    template_name = "admin/course/coursesessionattendancemodel/export_form.html"
    permission_check_method = "_has_lab_employee_permission"
    export_filename_prefix = "course_session_attendance"

    def _get_base_queryset(self, request) -> QuerySet:
        """
        Get base queryset with optimizations and security filters.

        - Select related for performance
        - Filter by is_active=True for non-superusers
        - Order by course, session date, student name
        """
        queryset = self.model.objects.select_related(
            "course_session__course", "student", "marked_by", "created_by", "updated_by"
        )

        # Non-superusers only see active attendance records
        if not getattr(request.user, "is_superuser", False):
            queryset = queryset.filter(is_active=True)

        return queryset.order_by(
            "course_session__course__title",
            "course_session__date",
            "student__first_name",
            "student__last_name",
        )

    def _apply_filters(self, queryset: QuerySet, form_data: Dict[str, Any]) -> QuerySet:
        """Apply filters based on form data."""

        # Course filtering
        course_id = form_data.get("course")
        if course_id:
            try:
                course = CourseModel.objects.get(id=course_id)
                queryset = queryset.filter(course_session__course=course)
            except CourseModel.DoesNotExist:
                pass

        # Course session filtering
        session_id = form_data.get("course_session")
        if session_id:
            try:
                session = CourseSessionModel.objects.get(id=session_id)
                queryset = queryset.filter(course_session=session)
            except CourseSessionModel.DoesNotExist:
                pass

        # Attendance status filtering
        status = form_data.get("attendance_status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def _get_template_context(self, request, form) -> Dict[str, Any]:
        """Get template context with course session attendance specific data."""
        context = super()._get_template_context(request, form)

        # Update title for course session attendance
        context.update(
            {
                "title": _("Export Course Session Attendance with Filters"),
                "module_name": _("Course Session Attendance"),
                "export_description": _(
                    "Export course session attendance data with customizable filters and field selection. "
                    "This includes course information, session details, student data, and attendance status."
                ),
            }
        )

        return context

    def _generate_filename(self, form_data: Dict[str, Any], file_format: str) -> str:
        """Generate filename with descriptive information."""

        # Base filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_parts = [self.export_filename_prefix, timestamp]

        # Add course if filtered
        course_id = form_data.get("course")
        if course_id:
            try:
                course = CourseModel.objects.get(id=course_id)
                course_name = course.title.replace(" ", "_").lower()
                filename_parts.append(f"course_{course_name}")
            except CourseModel.DoesNotExist:
                pass

        # Add session if filtered
        session_id = form_data.get("course_session")
        if session_id:
            try:
                session = CourseSessionModel.objects.get(id=session_id)
                session_name = session.title.replace(" ", "_").lower()
                filename_parts.append(f"session_{session_name}")
            except CourseSessionModel.DoesNotExist:
                pass

        # Add attendance status if filtered
        status = form_data.get("attendance_status")
        if status:
            filename_parts.append(f"status_{status.lower()}")

        return f"{'_'.join(filename_parts)}.{file_format}"

    def _has_lab_employee_permission(self, request):
        """Override to include asisten for export access."""
        if getattr(request.user, "is_superuser", False):
            return True

        # Only superuser and asisten can export
        allowed_groups = [UserGroup.LABORATORY_ASSISTANT]
        return has_group_permission(request.user, allowed_groups)

    def _check_permissions(self, request) -> bool:
        """Override to include asisten for export access."""
        if getattr(request.user, "is_superuser", False):
            return True

        # Only superuser and asisten can export
        allowed_groups = [UserGroup.LABORATORY_ASSISTANT]
        return has_group_permission(request.user, allowed_groups)
