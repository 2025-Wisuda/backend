# filepath: /Users/cg/Documents/MVP ONLY/room_booking/rest/views/room_booking_views.py
"""
This module provides ViewSet classes for room booking operations,
including CRUD operations and approval workflow.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from core import ApprovalStatus, UserGroup
from shared.presenter import ResponsePresenter
from shared.utils import owner_only, owner_or_laboratory_staff, technician_or_higher
from shared.utils.permission_config_utils import has_group_permission

from ...models import RoomBookingModel
from ..filters import RoomBookingFilter
from ..schemas.room_booking_schema import (
    room_booking_approval_schema,
    room_booking_create_schema,
    room_booking_delete_schema,
    room_booking_detail_schema,
    room_booking_list_schema,
    room_booking_update_schema,
)
from ..serializers import (
    RoomBookingApprovalSerializer,
    RoomBookingDetailSerializer,
    RoomBookingListSerializer,
)


class RoomBookingViewSet(ModelViewSet):
    """
    ViewSet for room booking operations.

    Provides:
    - list: Get paginated list of room bookings with filtering
    - create: Create new room booking
    - retrieve: Get detailed view of specific room booking
    - update/partial_update: Update room booking (only when status is pending)
    - destroy: Cancel room booking (only when status is pending, changes to canceled)
    - approve: Approve room booking (technicians only)
    """

    http_method_names = ["get", "post", "patch", "head", "options", "delete"]

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = RoomBookingFilter
    ordering_fields = [
        "booking_date",
        "created_at",
    ]
    ordering = ["-booking_date", "-booking_start_time"]
    search_fields = [
        "purpose",
        "research_title",
        "booker__first_name",
        "booker__last_name",
        "supervisor_main",
        "examiner",
    ]

    def get_queryset(self):
        """
        Get queryset based on user permissions.
        - Laboratory staff can see all active bookings
        - Other users can only see their own active bookings
        """
        queryset = (
            RoomBookingModel.objects.filter(is_active=True)
            .select_related("booker", "approved_by_user")
            .order_by("-booking_date", "-booking_start_time")
        )

        # Check if user has laboratory staff permissions
        # laboratory_staff_groups = [
        #     UserGroup.LABORATORY_HEAD,
        #     UserGroup.LABORATORY_TECHNICIAN,
        #     UserGroup.LABORATORY_ASSISTANT,
        # ]

        if not has_group_permission(self.request.user, 
                                    # laboratory_staff_groups
                                    ):
            queryset = queryset.filter(booker=self.request.user)

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return RoomBookingListSerializer
        elif self.action == "approve":
            return RoomBookingApprovalSerializer
        return RoomBookingDetailSerializer

    @room_booking_list_schema
    def list(self, request, *args, **kwargs):
        """List room bookings with pagination, filtering, and search."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return ResponsePresenter.success_response(
            message="Room bookings retrieved successfully", data=serializer.data
        )

    @room_booking_create_schema
    def create(self, request, *args, **kwargs):
        """Create new room booking."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save(booker=request.user)
            response_serializer = RoomBookingDetailSerializer(instance)
            return ResponsePresenter.success_response(
                message="Room booking created successfully",
                data=response_serializer.data,
            )
        return ResponsePresenter.bad_request_response(
            message="Failed to create room booking", errors=serializer.errors
        )

    @room_booking_detail_schema
    # @owner_or_laboratory_staff
    def retrieve(self, request, *args, **kwargs):
        """Retrieve detailed room booking information."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ResponsePresenter.success_response(
            message="Room booking details retrieved successfully", data=serializer.data
        )

    @room_booking_update_schema
    # @owner_only
    def partial_update(self, request, *args, **kwargs):
        """Update room booking (only when status is pending)."""
        instance = self.get_object()

        # Check if booking is still pending
        if instance.booking_approval_status != ApprovalStatus.PENDING.value:
            return ResponsePresenter.bad_request_response(
                message="You can only update pending bookings"
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            updated_instance = serializer.save()
            response_serializer = RoomBookingDetailSerializer(updated_instance)
            return ResponsePresenter.success_response(
                message="Room booking updated successfully",
                data=response_serializer.data,
            )
        return ResponsePresenter.bad_request_response(
            message="Failed to update room booking", errors=serializer.errors
        )

    @room_booking_delete_schema
    # @owner_only
    def destroy(self, request, *args, **kwargs):
        """Cancel room booking (changes status to canceled, only when pending)."""
        instance = self.get_object()

        # Check if booking is still pending
        if instance.booking_approval_status != ApprovalStatus.PENDING.value:
            return ResponsePresenter.bad_request_response(
                message="You can only cancel pending bookings"
            )

        # Change status to rejected (canceled) instead of deleting
        instance.booking_approval_status = ApprovalStatus.CANCELLED.value
        instance.approval_notes = "Canceled by user"
        instance.save()

        return ResponsePresenter.success_response(
            message="Room booking canceled successfully"
        )

    @room_booking_approval_schema
    @action(detail=True, methods=["post"], url_path="approve")
    # @technician_or_higher
    def approve(self, request, pk=None):
        """Approve a specific booking (technicians only)."""
        instance = self.get_object()

        # Check if booking is still pending
        if instance.booking_approval_status != ApprovalStatus.PENDING.value:
            return ResponsePresenter.bad_request_response(
                message="Only pending bookings can be approved"
            )

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Use the ApprovalMixin method
            notes = serializer.validated_data.get(
                "approval_notes", "Approved by technician"
            )
            instance.approve(approved_by=request.user, notes=notes)
            instance.save()

            response_serializer = RoomBookingDetailSerializer(instance)
            return ResponsePresenter.success_response(
                message="Room booking approved successfully",
                data=response_serializer.data,
            )

        return ResponsePresenter.bad_request_response(
            message="Failed to approve room booking", errors=serializer.errors
        )
