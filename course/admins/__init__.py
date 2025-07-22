"""Course admin configurations."""

from .course_admin import CourseAdmin
from .course_resource import CourseResource, CourseSessionResource
from .course_session_admin import CourseSessionAdmin
from .course_session_attendance_admin import CourseSessionAttendanceAdmin

__all__ = [
    "CourseAdmin",
    "CourseSessionAdmin",
    "CourseSessionAttendanceAdmin",
    "CourseResource",
    "CourseSessionResource",
]
