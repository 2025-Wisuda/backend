"""
Course Session Attendance resource for import/export operations.

Defines the fields and dehydration methods for exporting course session attendance data.
"""

from django.utils.translation import gettext_lazy as _
from import_export import fields, resources

from ..models import CourseSessionAttendanceModel


class CourseSessionAttendanceResource(resources.ModelResource):
    """
    Resource for course session attendance data export.
    
    Provides field mapping and data transformation for export operations.
    """
    
    # Custom field definitions
    course_title = fields.Field(
        column_name=_("Course Title"),
        attribute="course_session__course__title"
    )
    
    course_session_title = fields.Field(
        column_name=_("Session Title"),
        attribute="course_session__title"
    )
    
    session_date = fields.Field(
        column_name=_("Session Date"),
        attribute="course_session__date"
    )
    
    session_time = fields.Field(
        column_name=_("Session Time"),
        attribute="get_session_time"
    )
    
    student_name = fields.Field(
        column_name=_("Student Name"),
        attribute="student"
    )
    
    student_number = fields.Field(
        column_name=_("Student Number"),
        attribute="student__student_number"
    )
    
    attendance_status = fields.Field(
        column_name=_("Attendance Status"),
        attribute="status"
    )
    
    marked_at = fields.Field(
        column_name=_("Marked At"),
        attribute="marked_at"
    )
    
    marked_by = fields.Field(
        column_name=_("Marked By"),
        attribute="marked_by"
    )

    class Meta:
        model = CourseSessionAttendanceModel
        fields = (
            "course_title",
            "course_session_title", 
            "session_date",
            "session_time",
            "student_name",
            "student_number",
            "attendance_status",
            "marked_at",
            "marked_by",
        )
        export_order = (
            "course_title",
            "course_session_title", 
            "session_date",
            "session_time",
            "student_name",
            "student_number",
            "attendance_status",
            "marked_at",
            "marked_by",
        )
        skip_unchanged = True
        report_skipped = False
        import_id_fields = []  # No import allowed - export only
        
    def dehydrate_student_name(self, attendance):
        """Format student name display."""
        if attendance.student:
            return f"{attendance.student.first_name} {attendance.student.last_name}"
        return ""
        
    def dehydrate_marked_by(self, attendance):
        """Format marked by user display."""
        if attendance.marked_by:
            return f"{attendance.marked_by.first_name} {attendance.marked_by.last_name}"
        return ""
        
    def dehydrate_attendance_status(self, attendance):
        """Format attendance status display."""
        if attendance.status:
            return attendance.get_status_display()
        return ""
        
    def dehydrate_marked_at(self, attendance):
        """Format marked at timestamp."""
        if attendance.marked_at:
            return attendance.marked_at.strftime("%Y-%m-%d %H:%M")
        return ""
        
    def get_session_time(self, attendance):
        """Get formatted session time."""
        if attendance.course_session:
            start_time = attendance.course_session.start_time
            end_time = attendance.course_session.end_time
            if start_time and end_time:
                return f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            elif start_time:
                return start_time.strftime('%H:%M')
        return "" 