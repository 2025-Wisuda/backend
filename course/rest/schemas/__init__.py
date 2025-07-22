"""API schemas for course management and session endpoints."""

from .course_schemas import (
    course_create_schema,
    course_destroy_schema,
    course_detail_schema,
    course_enroll_schema,
    course_list_schema,
    course_my_courses_schema,
    course_update_schema,
)
from .course_session_attendance_schemas import (
    course_session_attendance_detail_schema,
    course_session_attendance_list_schema,
    course_session_attendance_manual_override_schema,
    course_session_attendance_personal_schema,
)
from .course_session_schemas import (
    course_session_create_schema,
    course_session_destroy_schema,
    course_session_detail_schema,
    course_session_update_schema,
)

__all__ = [
    "course_list_schema",
    "course_detail_schema",
    "course_create_schema",
    "course_update_schema",
    "course_destroy_schema",
    "course_enroll_schema",
    "course_my_courses_schema",
    "course_session_detail_schema",
    "course_session_create_schema",
    "course_session_update_schema",
    "course_session_destroy_schema",
    "course_session_attendance_list_schema",
    "course_session_attendance_detail_schema",
    "course_session_attendance_personal_schema",
    "course_session_attendance_manual_override_schema",
]
