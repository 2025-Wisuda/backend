"""
API schema definitions for room booking endpoints.

This module defines OpenAPI schema decorators for room booking API endpoints
including listing, creation, update, approval/rejection, and detail views using drf-spectacular.
"""

from core.enums import ApprovalStatus, BookingType
from drf_spectacular.utils import OpenApiParameter, extend_schema
from shared.schemas import ResponseSchema

from ..serializers import (
    RoomBookingApprovalSerializer,
    RoomBookingDetailSerializer,
    RoomBookingListSerializer,
)

# Basic CRUD Operations
room_booking_list_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        RoomBookingListSerializer, name="RoomBookingListResponse"
    ),
    parameters=[
        # Date filtering parameters
        OpenApiParameter(
            "date",
            type=str,
            description="Filter by specific booking date (YYYY-MM-DD format)",
            required=False,
        ),
        # Booking type filtering
        OpenApiParameter(
            "booking_type",
            type=str,
            description=f"Filter by booking type. Available options: {', '.join([bt.value for bt in BookingType])}",
            required=False,
            enum=[bt.value for bt in BookingType],
        ),
        # Approval status filtering
        OpenApiParameter(
            "approval_status",
            type=str,
            description=f"Filter by approval status. Available options: {', '.join([status.value for status in ApprovalStatus])}",
            required=False,
            enum=[status.value for status in ApprovalStatus],
        ),
        # Search parameters
        OpenApiParameter(
            "search",
            type=str,
            description="Search in purpose and research title fields",
            required=False,
        ),
        # Ordering parameters
        OpenApiParameter(
            "ordering",
            type=str,
            description="Order by fields: date,  created_at (prefix with '-' for desc)",
            required=False,
        ),
    ],
    summary="List room bookings",
    description="Retrieve a paginated list of room bookings with filtering, search, and ordering capabilities.",
    tags=["Room Booking"],
)

room_booking_create_schema = extend_schema(
    request=RoomBookingDetailSerializer,
    responses=ResponseSchema.get_response_schema(
        RoomBookingDetailSerializer, name="RoomBookingCreateResponse"
    ),
    summary="Create room booking",
    description=f"Create a new room booking. Academic fields are required for {BookingType.SEMINAR.value} bookings by students/assistants. Staff/faculty can create any booking type with basic information only.",
    tags=["Room Booking"],
)

room_booking_detail_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        RoomBookingDetailSerializer, name="RoomBookingDetailResponse"
    ),
    summary="Retrieve room booking details",
    description="Get detailed information about a specific room booking including all academic details and approval status.",
    tags=["Room Booking"],
)

room_booking_update_schema = extend_schema(
    request=RoomBookingDetailSerializer,
    responses=ResponseSchema.get_response_schema(
        RoomBookingDetailSerializer, name="RoomBookingUpdateResponse"
    ),
    summary="Update room booking",
    description="Update an existing room booking. Only the booking owner can update their own bookings. Approval fields cannot be modified through this endpoint.",
    tags=["Room Booking"],
)

room_booking_delete_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        RoomBookingDetailSerializer, name="RoomBookingDeleteResponse"
    ),
    summary="Cancel room booking",
    description=f"Cancel an existing room booking. Only bookings with {ApprovalStatus.PENDING.value} status can be canceled, which changes their status to {ApprovalStatus.CANCELLED.value}.",
    tags=["Room Booking"],
)

room_booking_approval_schema = extend_schema(
    request=RoomBookingApprovalSerializer,
    responses=ResponseSchema.get_response_schema(
        RoomBookingDetailSerializer, name="RoomBookingApprovalResponse"
    ),
    summary="Approve room booking",
    description="Approve a room booking (technicians only). Approval notes are optional but recommended for record keeping.",
    tags=["Room Booking"],
)

room_booking_rejection_schema = extend_schema(
    request=RoomBookingApprovalSerializer,
    responses=ResponseSchema.get_response_schema(
        RoomBookingDetailSerializer, name="RoomBookingRejectionResponse"
    ),
    summary="Reject room booking",
    description="Reject a room booking (technicians only). Rejection notes are required to explain the reason for rejection.",
    tags=["Room Booking"],
)
