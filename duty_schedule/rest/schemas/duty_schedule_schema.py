"""
API schema definitions for duty schedule endpoints.

This module defines OpenAPI schema decorators for duty schedule API endpoints
including listing and detail views using drf-spectacular.
"""

from drf_spectacular.utils import OpenApiParameter, extend_schema

from core.enums.days_enum import DaysEnum
from shared.schemas import ResponseSchema

from ..serializers import DutyScheduleSerializer

# Public duty schedule list schema (for lab schedule view)
duty_schedule_list_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        DutyScheduleSerializer, name="DutyScheduleListResponse"
    ),
    parameters=[
        OpenApiParameter(
            "duty_days",
            type=str,
            description="Filter by days pattern. Available options based on DaysEnum choices (Indonesian day names)",
            required=False,
            enum=[day.value for day in DaysEnum],
        )
    ],
    summary="List duty schedules",
    description="Retrieve a paginated list of duty schedules with filtering and search capabilities for lab schedule display and integration.",
    tags=["Duty Schedules"],
)


duty_schedule_today_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        DutyScheduleSerializer, name="DutyScheduleTodayResponse"
    ),
    summary="Today's Duty Schedule",
    description="Retrieve today's duty schedule with attendance status for mobile-friendly display. Includes assigned laboratory assistants and their attendance status.",
    tags=["Duty Schedules"],
)
