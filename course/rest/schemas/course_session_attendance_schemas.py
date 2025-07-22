"""OpenAPI schema definitions for course session attendance endpoints."""

from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from shared.schemas import ResponseSchema

from ..serializers import (
    CourseSessionAttendanceDetailSerializer,
    CourseSessionAttendanceListSerializer,
    CourseSessionAttendanceManualOverrideSerializer,
    CourseSessionAttendancePersonalSerializer,
)

course_session_attendance_list_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        CourseSessionAttendanceListSerializer,
        name="CourseSessionAttendanceListResponse",
    ),
    parameters=[
        OpenApiParameter(
            "search",
            type=str,
            description="Search by student first name, last name, username, or student number",
            required=False,
        ),
    ],
    summary="List course session attendances",
    description="Retrieve a paginated list of course session attendances with search capabilities.",
    tags=["Course Session Attendance"],
)

course_session_attendance_detail_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        CourseSessionAttendanceDetailSerializer,
        name="CourseSessionAttendanceDetailResponse",
    ),
    summary="Retrieve course session attendance details",
    description="Get detailed information about a specific course session attendance record.",
    tags=["Course Session Attendance"],
)

course_session_attendance_manual_override_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        CourseSessionAttendanceManualOverrideSerializer,
        name="CourseSessionAttendanceManualOverrideResponse",
    ),
    summary="Manual override attendance",
    description="Manually mark attendance for a student. Only accessible by TAs assigned to the course.",
    tags=["Course Session Attendance"],
)

course_session_attendance_personal_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        CourseSessionAttendancePersonalSerializer,
        name="CourseSessionAttendancePersonalResponse",
    ),
    summary="Get personal attendance record",
    description="Retrieve a single attendance record for the authenticated student and course session.",
    tags=["Course Session Attendance"],
)
