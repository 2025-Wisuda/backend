"""
Course Session Attendance Export Form for Django admin.

Provides filtering options for exporting course session attendance data with:
- Course filtering
- Course session filtering
- Date filtering
- Student filtering
- Field selection with checkboxes
"""

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from core.enums import AttendanceStatus, Month
from shared.export import BaseExportForm, ModelSpecificExportFormMixin

from ...models import CourseModel, CourseSessionAttendanceModel, CourseSessionModel
from ..course_session_attendance_resource import CourseSessionAttendanceResource

User = get_user_model()


class CourseSessionAttendanceExportForm(BaseExportForm, ModelSpecificExportFormMixin):
    """
    Course Session Attendance-specific export form with filtering and field selection.

    Features:
    - Course filtering
    - Course session filtering
    - Attendance status filtering
    - Field selection with checkboxes
    """
    
    # Disable default date filtering - we only need course/session filters
    SHOW_DATE_FILTERING = False

    # Field selection - from CourseSessionAttendanceResource
    FIELD_CHOICES = [
        (field, _(field.replace("_", " ").title()))
        for field in CourseSessionAttendanceResource._meta.fields
    ]

    # Default selected fields for user convenience
    DEFAULT_FIELDS = [
        "course_title",
        "course_session_title",
        "session_date",
        "session_time",
        "student_name", 
        "student_number",
        "attendance_status",
    ]

    def _setup_custom_fields(self):
        """Setup course session attendance specific fields."""
        
        # Add course filtering
        courses = CourseModel.objects.filter(
            is_active=True
        ).order_by("title")

        course_choices = [("", _("All Courses"))]
        course_choices.extend([
            (str(course.id), course.title)
            for course in courses
        ])
        
        self.add_choice_filter("course", course_choices, _("Course"))

        # Add course session filtering
        sessions = CourseSessionModel.objects.filter(
            is_active=True
        ).select_related("course").order_by("course__title", "date", "title")

        session_choices = [("", _("All Sessions"))]
        session_choices.extend([
            (str(session.id), f"{session.course.title} - {session.title} ({session.date})")
            for session in sessions
        ])
        
        self.add_choice_filter("course_session", session_choices, _("Course Session"))

        # Add attendance status filtering
        status_choices = [("", _("All Statuses"))]
        status_choices.extend(AttendanceStatus.choices())
        self.add_choice_filter(
            "attendance_status", 
            status_choices, 
            _("Attendance Status")
        )

    def _clean_custom(self, cleaned_data):
        """Custom validation for course session attendance export form."""
        # No custom validation needed for course/session filtering
        return cleaned_data

    def _get_custom_filter_summary(self, data):
        """
        Get summary of applied custom filters for display.
        """
        summary = []

        # Course filter
        course_id = data.get("course")
        if course_id:
            try:
                course = CourseModel.objects.get(id=course_id)
                summary.append(f"Course: {course.title}")
            except CourseModel.DoesNotExist:
                pass

        # Course session filter
        session_id = data.get("course_session")
        if session_id:
            try:
                session = CourseSessionModel.objects.select_related("course").get(id=session_id)
                summary.append(f"Session: {session.course.title} - {session.title}")
            except CourseSessionModel.DoesNotExist:
                pass

        # Attendance status filter
        status = data.get("attendance_status")
        if status:
            summary.append(f"Status: {status}")

        return summary 