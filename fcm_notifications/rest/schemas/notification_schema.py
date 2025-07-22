from drf_spectacular.utils import OpenApiParameter, extend_schema
from shared.schemas import ResponseSchema

from ..serializers.notification_log_serializer import (
    NotificationMarkAllAsReadResponseSerializer,
    NotificationMarkAsReadResponseSerializer,
    NotificationUnreadCountResponseSerializer,
    NotificationLogListSerializer
)

notification_list_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        NotificationLogListSerializer, name="NotificationListResponse"
    ),
    parameters=[
        OpenApiParameter(
            "search", type=str, description="Search in title/body", required=False
        ),
        OpenApiParameter(
            "type", type=str, description="Filter by notification type", required=False
        ),
        OpenApiParameter(
            "is_read",
            type=str,
            description='Filter by read status ("true"/"false")',
            required=False,
        ),
        OpenApiParameter(
            "ordering",
            type=str,
            description="Order by sent_at (prefix with '-' for desc)",
            required=False,
        ),
    ],
    summary="List notifications",
    description="Retrieve a paginated list of notifications with filtering, search, and ordering.",
    tags=["Notification"],
)

notification_mark_as_read_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        NotificationMarkAsReadResponseSerializer, name="NotificationMarkAsReadResponse"
    ),
    summary="Mark notification as read",
    description="Mark a specific notification as read by ID.",
    tags=["Notification"],
)

notification_mark_all_as_read_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        NotificationMarkAllAsReadResponseSerializer,
        name="NotificationMarkAllAsReadResponse",
    ),
    summary="Mark all notifications as read",
    description="Mark all notifications for the current user as read.",
    tags=["Notification"],
)

notification_unread_count_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        NotificationUnreadCountResponseSerializer,
        name="NotificationUnreadCountResponse",
    ),
    summary="Get unread notification count",
    description="Retrieve the count of unread notifications for the current user.",
    tags=["Notification"],
)
