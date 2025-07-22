"""OpenAPI schema definitions for lab schedule aggregator endpoints."""

from drf_spectacular.utils import OpenApiParameter, extend_schema

from core.enums import ActivityType
from shared.schemas import ResponseSchema

from ..serializers import (
    AvailableTimeSlotSerializer,
    LabScheduleDetailSerializer,
    LabScheduleListSerializer,
)

lab_schedule_list_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        LabScheduleListSerializer, name="LabScheduleListResponse"
    ),
    parameters=[
        OpenApiParameter(
            "type",
            type=str,
            description=f"Filter by activity type. Available options: {', '.join([at.value for at in ActivityType])}",
            required=False,
            enum=[at.value for at in ActivityType],
        ),
        OpenApiParameter(
            "date",
            type=str,
            description="Filter by scheduled date (YYYY-MM-DD format)",
            required=False,
        ),
        OpenApiParameter(
            "search",
            type=str,
            description="Search in activity type and details",
            required=False,
        ),
    ],
    summary="List aggregated lab schedules",
    description="Retrieve a paginated list of aggregated lab schedules from all booking types with filtering and search capabilities.",
    tags=["Lab Schedule"],
)

lab_schedule_detail_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        LabScheduleDetailSerializer, name="LabScheduleDetailResponse"
    ),
    summary="Retrieve aggregated lab schedule details",
    description="Get detailed information about a specific aggregated lab schedule including source model and creator details.",
    tags=["Lab Schedule"],
)

lab_schedule_availability_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        AvailableTimeSlotSerializer, name="LabScheduleAvailabilityResponse"
    ),
    parameters=[
        OpenApiParameter(
            "date",
            type=str,
            description="Date to check availability (YYYY-MM-DD format)",
            required=True,
        ),
    ],
    summary="Check lab availability",
    description="Get available time slots for a specific date based on all aggregated schedules and lab operating hours.",
    tags=["Lab Schedule"],
)

lab_schedule_my_schedules_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        LabScheduleListSerializer, name="LabScheduleMySchedulesResponse"
    ),
    summary="Get current user's today lab schedules",
    description="Retrieve today's lab schedules related to the current user. Includes schedules from CourseSession (where user is enrolled student or assigned TA), RoomBooking (where user is booker), and LabAllocation (where user is creator).",
    tags=["Lab Schedule"],
)
