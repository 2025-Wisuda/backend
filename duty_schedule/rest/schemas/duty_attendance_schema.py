"""
API schema definitions for duty attendance endpoints.

This module defines OpenAPI schema decorators for duty attendance API endpoints
including listing, details, clock in/out operations, and OTP validation using drf-spectacular.
"""

from drf_spectacular.utils import OpenApiParameter, extend_schema

from core.enums import AttendanceStatus
from core.enums.days_enum import DaysEnum
from shared.schemas import ResponseSchema

from ..serializers import (
    DutyAttendanceClockInSerializer,
    DutyAttendanceClockOutSerializer,
    DutyAttendanceDetailSerializer,
    DutyAttendanceListSerializer,
    DutyAttendancePersonalSerializer,
    DutyOTPSerializer,
)

# Admin duty attendance list schema
duty_attendance_list_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        DutyAttendanceListSerializer, name="DutyAttendanceListResponse"
    ),
    parameters=[
        OpenApiParameter(
            "duty_date",
            type=str,
            description="Filter by specific duty date (YYYY-MM-DD format)",
            required=False,
        ),
        OpenApiParameter(
            "attendance_status",
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


# Clock in schema
duty_attendance_clock_in_schema = extend_schema(
    request=DutyAttendanceClockInSerializer,
    responses=ResponseSchema.get_response_schema(
        DutyAttendanceDetailSerializer, name="DutyAttendanceClockInResponse"
    ),
    summary="Clock in for duty (Manual)",
    description="Manual clock in for duty attendance. OTP must be validated separately before using this endpoint. Optional location data and notes can be provided for record keeping.",
    tags=["Duty Attendance"],
)

# Personal attendance schema for /me endpoint
duty_attendance_personal_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        DutyAttendancePersonalSerializer, name="DutyAttendancePersonalResponse"
    ),
    parameters=[
        OpenApiParameter(
            "duty_date",
            type=str,
            description="Filter by specific duty date (YYYY-MM-DD format)",
            required=False,
        ),
        OpenApiParameter(
            "attendance_status",
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

# Clock out schema
duty_attendance_clock_out_schema = extend_schema(
    request=DutyAttendanceClockOutSerializer,
    responses=ResponseSchema.get_response_schema(
        DutyAttendanceDetailSerializer, name="DutyAttendanceClockOutResponse"
    ),
    summary="Clock out from duty (Manual)",
    description="Manual clock out from duty attendance. OTP must be validated separately before using this endpoint. Optional location data and notes can be provided for record keeping.",
    tags=["Duty Attendance"],
)
