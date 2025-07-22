"""
Clean Notification Views - Only endpoints that mobile actually needs
"""

import logging

from drf_spectacular.utils import extend_schema
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from shared.pagination.custom_pagination import CustomPagination
from shared.presenter import ResponsePresenter

from ...models import NotificationLogModel
from ..filters.notification_filter import NotificationLogFilter
from ..schemas.notification_schema import (
    notification_list_schema,
    notification_mark_all_as_read_schema,
    notification_mark_as_read_schema,
    notification_unread_count_schema,
)
from ..serializers.notification_log_serializer import (
    NotificationLogListSerializer,
    NotificationMarkAllAsReadResponseSerializer,
    NotificationMarkAsReadResponseSerializer,
    NotificationUnreadCountResponseSerializer,
)

logger = logging.getLogger(__name__)


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for notification endpoints (list, mark as read, mark all as read, unread count).
    """

    serializer_class = NotificationLogListSerializer
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NotificationLogFilter
    search_fields = ["title", "body"]
    ordering_fields = ["sent_at"]
    ordering = ["-sent_at"]

    def get_queryset(self):
        queryset = NotificationLogModel.objects.filter(user=self.request.user)
        return queryset

    @extend_schema(exclude=True)
    def retrieve(self, request, *args, **kwargs):
        return ResponsePresenter.bad_request_response(message="Not implemented.")

    @notification_list_schema
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return ResponsePresenter.success_response(
            message="Notifications retrieved successfully", data=serializer.data
        )

    @notification_mark_as_read_schema
    @action(detail=True, methods=["post"], url_path="mark-as-read")
    def mark_as_read(self, request, pk=None):
        try:
            notification = self.get_object()
            notification.is_read = True
            notification.save(update_fields=["is_read"])
            serializer = NotificationMarkAsReadResponseSerializer(
                {"id": notification.id}
            )
            return ResponsePresenter.success_response(
                message=f"Notification {notification.id} marked as read",
                data=serializer.data,
            )
        except NotificationLogModel.DoesNotExist:
            return ResponsePresenter.not_found_response(
                message="Notification not found"
            )
        except Exception as e:
            return ResponsePresenter.internal_server_error_response(
                message="Failed to mark notification as read"
            )

    @notification_mark_all_as_read_schema
    @action(detail=False, methods=["post"], url_path="mark-all-as-read")
    def mark_all_as_read(self, request):
        try:
            updated_count = NotificationLogModel.objects.filter(
                user=request.user, is_read=False
            ).update(is_read=True)
            serializer = NotificationMarkAllAsReadResponseSerializer(
                {"updated_count": updated_count}
            )
            return ResponsePresenter.success_response(
                message=f"Marked {updated_count} notifications as read",
                data=serializer.data,
            )
        except Exception as e:
            return ResponsePresenter.internal_server_error_response(
                message="Failed to mark all notifications as read"
            )

    @notification_unread_count_schema
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        try:
            unread_count = NotificationLogModel.objects.filter(
                user=request.user, is_read=False
            ).count()
            serializer = NotificationUnreadCountResponseSerializer(
                {"unread_count": unread_count}
            )
            return ResponsePresenter.success_response(
                message="Unread notification count retrieved successfully",
                data=serializer.data,
            )
        except Exception as e:
            return ResponsePresenter.internal_server_error_response(
                message="Failed to get unread count"
            )
