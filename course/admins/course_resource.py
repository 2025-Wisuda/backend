"""
Import/Export resources for Course models.

This module provides import/export functionality for course management,
following the established patterns in the project.
"""

from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from custom_auth.models import CustomUserModel

from ..models import CourseModel, CourseSessionModel


class CourseResource(resources.ModelResource):
    """Resource for Course model import/export."""

    # Custom fields for better export display
    created_by = fields.Field(
        column_name="Created By",
        attribute="created_by",
        widget=ForeignKeyWidget(CustomUserModel, field="username"),
    )

    updated_by = fields.Field(
        column_name="Updated By",
        attribute="updated_by",
        widget=ForeignKeyWidget(CustomUserModel, field="username"),
    )

    enrolled_students = fields.Field(
        column_name="Enrolled Students",
        attribute="enrolled_students",
        widget=ManyToManyWidget(CustomUserModel, field="username", separator=", "),
    )

    teaching_assistants = fields.Field(
        column_name="Teaching Assistants",
        attribute="teaching_assistants",
        widget=ManyToManyWidget(CustomUserModel, field="username", separator=", "),
    )

    class Meta:
        model = CourseModel
        fields = (
            "id",
            "title",
            "description",
            "start_date",
            "end_date",
            "enroll_key",
            "total_sessions",
            "completed_sessions",
            "enrolled_students",
            "teaching_assistants",
            "is_active",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        )
        export_order = (
            "title",
            "description",
            "start_date",
            "end_date",
            "total_sessions",
            "completed_sessions",
            "enrolled_students",
            "teaching_assistants",
            "enroll_key",
            "is_active",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        )
        import_id_fields = ("id",)
        skip_unchanged = True
        report_skipped = False

    def dehydrate_title(self, course):
        """Format course title for export."""
        return course.title or ""

    def dehydrate_description(self, course):
        """Format course description for export."""
        return course.description or ""

    def dehydrate_start_date(self, course):
        """Format start date for export."""
        return course.start_date.strftime("%Y-%m-%d") if course.start_date else ""

    def dehydrate_end_date(self, course):
        """Format end date for export."""
        return course.end_date.strftime("%Y-%m-%d") if course.end_date else ""

    def dehydrate_created_at(self, course):
        """Format created date for export."""
        return (
            course.created_at.strftime("%Y-%m-%d %H:%M:%S") if course.created_at else ""
        )

    def dehydrate_updated_at(self, course):
        """Format updated date for export."""
        return (
            course.updated_at.strftime("%Y-%m-%d %H:%M:%S") if course.updated_at else ""
        )


class CourseSessionResource(resources.ModelResource):
    """Resource for Course Session model import/export."""

    # Custom fields for better export display
    course = fields.Field(
        column_name="Course",
        attribute="course",
        widget=ForeignKeyWidget(CourseModel, field="title"),
    )

    created_by = fields.Field(
        column_name="Created By",
        attribute="created_by",
        widget=ForeignKeyWidget(CustomUserModel, field="username"),
    )

    updated_by = fields.Field(
        column_name="Updated By",
        attribute="updated_by",
        widget=ForeignKeyWidget(CustomUserModel, field="username"),
    )

    class Meta:
        model = CourseSessionModel
        fields = (
            "id",
            "course",
            "title",
            "description",
            "date",
            "start_time",
            "end_time",
            "session_status",
            "is_active",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        )
        export_order = (
            "course",
            "title",
            "description",
            "date",
            "start_time",
            "end_time",
            "session_status",
            "is_active",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        )
        import_id_fields = ("id",)
        skip_unchanged = True
        report_skipped = False

    def dehydrate_title(self, session):
        """Format session title for export."""
        return session.title or ""

    def dehydrate_description(self, session):
        """Format session description for export."""
        return session.description or ""

    def dehydrate_date(self, session):
        """Format session date for export."""
        return session.date.strftime("%Y-%m-%d") if session.date else ""

    def dehydrate_start_time(self, session):
        """Format start time for export."""
        return session.start_time.strftime("%H:%M:%S") if session.start_time else ""

    def dehydrate_end_time(self, session):
        """Format end time for export."""
        return session.end_time.strftime("%H:%M:%S") if session.end_time else ""

    def dehydrate_created_at(self, session):
        """Format created date for export."""
        return (
            session.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if session.created_at
            else ""
        )

    def dehydrate_updated_at(self, session):
        """Format updated date for export."""
        return (
            session.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            if session.updated_at
            else ""
        )
