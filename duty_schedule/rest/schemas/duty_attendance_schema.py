"""
API schema definitions for duty attendance endpoints.

This module defines OpenAPI schema decorators for duty attendance API endpoints
including listing, details, clock in/out operations, and OTP validation using drf-spectacular.
"""

from core.enums import AttendanceStatus
from core.enums.days_enum import DaysEnum
from drf_spectacular.utils import OpenApiParameter, extend_schema
from shared.schemas import ResponseSchema

from ..serializers import (
    DutyAttendanceDetailSerializer,
    DutyAttendanceListSerializer,
    DutyAttendanceManualOverrideSerializer,
    DutyAttendancePersonalSerializer,
    DutyAttendanceStatisticsSerializer,
    DutyOTPSerializer,
)

# Admin duty attendance list schema
duty_attendance_list_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        DutyAttendanceListSerializer, name="DutyAttendanceListResponse"
    ),
    parameters=[
        OpenApiParameter(
            "date",
            type=str,
            description="Filter by specific duty date (YYYY-MM-DD format)",
            required=False,
        ),
        OpenApiParameter(
            "status",
            type=str,
            description=f"Filter by attendance status. Available options: {', '.join([status.value for status in AttendanceStatus])}",
            required=False,
            enum=[status.value for status in AttendanceStatus],
        ),
    ],
    summary="List duty attendance records (Admin)",
    description="Retrieve a paginated list of all duty attendance records for administrative purposes. Returns duty date with laboratory assistant details including name, student number, and attendance status. Use /me endpoint for personal attendance records.",
    tags=["Duty Attendance"],
)

# Duty attendance detail schema
duty_attendance_detail_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        DutyAttendanceDetailSerializer, name="DutyAttendanceDetailResponse"
    ),
    summary="Retrieve duty attendance details (Admin)",
    description="Get detailed information about a specific duty attendance record for administrative purposes. Returns duty date with laboratory assistant details including name, student number, attendance status, and clock in/out times. Users can only view their own records unless they have admin privileges.",
    tags=["Duty Attendance"],
)


# OTP validation schema
duty_otp_validation_schema = extend_schema(
    request=DutyOTPSerializer,
    responses=ResponseSchema.get_response_schema(
        DutyOTPSerializer, name="DutyOTPValidationResponse"
    ),
    summary="Validate duty OTP",
    description="Validate a 6-digit OTP code for duty attendance verification. This must be done before clock in/out operations.",
    tags=["Duty Attendance"],
)


# Personal attendance schema for /me endpoint
duty_attendance_personal_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        DutyAttendancePersonalSerializer, name="DutyAttendancePersonalResponse"
    ),
    parameters=[
        OpenApiParameter(
            "date",
            type=str,
            description="Filter by specific duty date (YYYY-MM-DD format)",
            required=False,
        ),
        OpenApiParameter(
            "status",
            type=str,
            description=f"Filter by attendance status. Available options: {', '.join([status.value for status in AttendanceStatus])}",
            required=False,
            enum=[status.value for status in AttendanceStatus],
        ),
    ],
    summary="Get personal attendance records (today and past only)",
    description="Retrieve a simplified list of the authenticated user's own duty attendance records for today and past dates only. Future attendance records are excluded since they haven't been performed yet. This endpoint provides basic duty information including laboratory, schedule times, and attendance status for mobile consumption.",
    tags=["Duty Attendance"],
)

# Manual override schema
duty_attendance_manual_override_schema = extend_schema(
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["clock_in", "clock_out"],
                    "description": "Action to perform: clock_in or clock_out",
                }
            },
            "required": ["action"],
        }
    },
    responses=ResponseSchema.get_response_schema(
        DutyAttendanceManualOverrideSerializer, name="DutyAttendanceManualOverrideResponse"
    ),
    summary="Manual attendance override",
    description="Manually override attendance status for a specific duty record. Only available to admin users or the attendance record owner. Requires action parameter (clock_in or clock_out).",
    tags=["Duty Attendance"],
)

# Statistics schema
duty_attendance_statistics_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        DutyAttendanceStatisticsSerializer, name="DutyAttendanceStatisticsResponse"
    ),
    parameters=[
        OpenApiParameter(
            "start_date",
            type=str,
            description="Start date for statistics (YYYY-MM-DD format). Defaults to 30 days ago.",
            required=False,
        ),
        OpenApiParameter(
            "end_date",
            type=str,
            description="End date for statistics (YYYY-MM-DD format). Defaults to today.",
            required=False,
        ),
        OpenApiParameter(
            "assistant_id",
            type=int,
            description="Filter statistics by specific laboratory assistant ID",
            required=False,
        ),
    ],
    summary="Get attendance statistics",
    description="Retrieve comprehensive attendance statistics including summary, status breakdown, daily trends, and assistant performance. Automatically updates expired attendance records before returning statistics. Only available to admin users.",
    tags=["Duty Attendance"],
)
