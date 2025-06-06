"""
This module provides ViewSet classes for lab schedule Aggregator,
including read-only operations and approval status updates.
"""

from datetime import datetime

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ReadOnlyModelViewSet

from shared.presenter import ResponsePresenter
from shared.utils import format_available_slots_for_api

from ...models import LabScheduleModel
from ..filters import LabScheduleFilter
from ..schemas import (
    lab_schedule_availability_schema,
    lab_schedule_detail_schema,
    lab_schedule_list_schema,
)
from ..serializers import (
    LabScheduleAvailabilitySerializer,
    LabScheduleDetailSerializer,
    LabScheduleListSerializer,
)


class LabScheduleViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for lab schedule Aggregator.

    Provides:
    - list: Get paginated list of lab schedules with filtering
    - retrieve: Get detailed view of specific lab schedule
    - availability: Check available time slots for a specific date
    """

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = LabScheduleFilter
    search_fields = ["activity_type", "activity_detail"]

    def get_queryset(self):
        """Get queryset with only active schedules."""
        return LabScheduleModel.objects.filter(is_active=True).order_by("-created_at")

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return LabScheduleListSerializer
        elif self.action == "retrieve":
            return LabScheduleDetailSerializer
        elif self.action == "availability":
            return LabScheduleAvailabilitySerializer
        return LabScheduleDetailSerializer

    @lab_schedule_list_schema
    def list(self, request, *args, **kwargs):
        """List lab schedules with pagination, filtering, and search."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return ResponsePresenter.success_response(
            message="Lab schedules retrieved successfully", data=serializer.data
        )

    @lab_schedule_detail_schema
    def retrieve(self, request, *args, **kwargs):
        """Retrieve detailed lab schedule information."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ResponsePresenter.success_response(
            message="Lab schedule details retrieved successfully", data=serializer.data
        )

    @lab_schedule_availability_schema
    @action(detail=False, methods=["get"], url_path="availability")
    def availability(self, request):
        """Check available time slots for a specific date."""
        date_str = request.query_params.get("date")
        if not date_str:
            return ResponsePresenter.bad_request_response(
                message="Date parameter is required",
            )

        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return ResponsePresenter.bad_request_response(
                message="Invalid date format. Use YYYY-MM-DD",
            )

        # Fetch approved lab schedules for the given date
        approved_schedules = LabScheduleModel.objects.filter(
            schedule_date=target_date,
        ).values_list("start_time", "end_time")

        # Convert to list of tuples for the utility function
        occupied_slots = list(approved_schedules)

        # Calculate available slots using the utility generator
        available_slots = format_available_slots_for_api(occupied_slots)

        # Create response data using serializer format
        response_data = {"date": target_date, "available_slots": available_slots}

        return ResponsePresenter.success_response(
            message=f"Lab availability for {date_str} retrieved successfully",
            data=response_data,
        )
