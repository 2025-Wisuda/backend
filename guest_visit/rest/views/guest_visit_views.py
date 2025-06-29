"""
ViewSet for Guest Visit operations.

Provides CRUD operations with conditional restrictions:
- No PUT method (only PATCH for partial updates)
- PATCH/DELETE only allowed within 5 minutes of creation
- Soft delete (set is_active = false) instead of hard delete
- Support for both manual entry and registered user visitor modes
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from shared.presenter import ResponsePresenter

from ...models import GuestVisitModel
from ..filters import GuestVisitFilter
from ..schemas import (
    guest_visit_create_schema,
    guest_visit_delete_schema,
    guest_visit_detail_schema,
    guest_visit_list_schema,
    guest_visit_update_schema,
)
from ..serializers import GuestVisitDetailSerializer, GuestVisitListSerializer


class GuestVisitViewSet(ModelViewSet):
    """
    ViewSet for guest visit operations.

    Provides:
    - list: Get paginated list of guest visits with filtering
    - create: Create new guest visit entry
    - retrieve: Get detailed view of specific guest visit
    - partial_update: Update guest visit (only within 5 minutes of creation)
    - destroy: Soft delete guest visit (only within 5 minutes of creation)

    Note: PUT method is disabled - only PATCH for partial updates
    """

    # Disable PUT method, only allow PATCH for updates
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = GuestVisitFilter
    ordering_fields = ["date", "start_time", "created_at"]
    ordering = ["-date", "-start_time"]
    search_fields = [
        "name",
        "visitor__first_name",
        "visitor__last_name",
        "visitor__username",
        "purpose",
    ]

    def get_queryset(self):
        """Get queryset with only active guest visits."""
        return (
            GuestVisitModel.objects.filter(is_active=True)
            .select_related("visitor", "created_by", "updated_by")
            .order_by("-date", "-start_time")
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return GuestVisitListSerializer
        return GuestVisitDetailSerializer

    @guest_visit_list_schema
    def list(self, request, *args, **kwargs):
        """List guest visits with pagination, filtering, and search."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return ResponsePresenter.success_response(
            message="Guest visits retrieved successfully", data=serializer.data
        )

    @guest_visit_create_schema
    def create(self, request, *args, **kwargs):
        """Create new guest visit entry."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save(created_by=request.user)
            response_serializer = GuestVisitDetailSerializer(instance)
            return ResponsePresenter.success_response(
                message="Guest visit created successfully",
                data=response_serializer.data,
            )
        return ResponsePresenter.bad_request_response(
            message="Failed to create guest visit", errors=serializer.errors
        )

    @guest_visit_detail_schema
    def retrieve(self, request, *args, **kwargs):
        """Retrieve detailed guest visit information."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ResponsePresenter.success_response(
            message="Guest visit details retrieved successfully", data=serializer.data
        )

    @guest_visit_update_schema
    def partial_update(self, request, *args, **kwargs):
        """Update guest visit (only within 5 minutes of creation)."""
        instance = self.get_object()

        # Check if still within 5-minute edit window
        if not instance.can_edit():
            return ResponsePresenter.bad_request_response(
                message="Guest visit can only be edited within 5 minutes of creation"
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            updated_instance = serializer.save(updated_by=request.user)
            response_serializer = GuestVisitDetailSerializer(updated_instance)
            return ResponsePresenter.success_response(
                message="Guest visit updated successfully",
                data=response_serializer.data,
            )
        return ResponsePresenter.bad_request_response(
            message="Failed to update guest visit", errors=serializer.errors
        )

    @guest_visit_delete_schema
    def destroy(self, request, *args, **kwargs):
        """Soft delete guest visit (only within 5 minutes of creation)."""
        instance = self.get_object()

        # Check if still within 5-minute edit window
        if not instance.can_edit():
            return ResponsePresenter.bad_request_response(
                message="Guest visit can only be deleted within 5 minutes of creation"
            )

        # Soft delete - set is_active to False
        instance.is_active = False
        instance.updated_by = request.user
        instance.save(update_fields=["is_active", "updated_by", "updated_at"])

        return ResponsePresenter.success_response(
            message="Guest visit deleted successfully"
        )
