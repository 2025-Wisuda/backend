"""
Lab schedule aggregator API with read-only operations and availability checking.

Key features:
- Read-only access to aggregated schedule data
- Filtering by activity type and date
- Available time slot calculation for booking assistance
- Performance optimized with active record filtering
"""

from datetime import datetime

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from shared.presenter import ResponsePresenter
from shared.utils import format_available_slots_for_api

from ...models import LabScheduleModel
from ..filters import LabScheduleFilter
from ..schemas import (
    lab_schedule_availability_schema,
    lab_schedule_detail_schema,
    lab_schedule_list_schema,
    lab_schedule_my_schedules_schema,
)
from ..serializers import (
    AvailableTimeSlotSerializer,
    LabScheduleDetailSerializer,
    LabScheduleListSerializer,
)


class LabScheduleViewSet(ReadOnlyModelViewSet):
    """
    Lab schedule aggregator with read-only operations and availability checking.

    Business features:
    - Read-only aggregated schedule data (no create/update/delete)
    - Activity type and date filtering capabilities
    - Available time slot calculation for booking forms
    - Performance optimization with active record filtering
    """

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = LabScheduleFilter
    search_fields = ["type", "detail"]

    def get_queryset(self):
        """
        Get queryset with only active schedules, ordered by schedule time.
        
        Ordering: date DESC, start_time DESC (most recent schedules first)
        This ensures consistent ordering between list and me endpoints.
        """
        return LabScheduleModel.objects.filter(is_active=True).order_by('-date', '-start_time')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return LabScheduleListSerializer
        elif self.action == "retrieve":
            return LabScheduleDetailSerializer
        elif self.action == "availability":
            return AvailableTimeSlotSerializer
        elif self.action == "me":
            return LabScheduleListSerializer
        return LabScheduleDetailSerializer

    @lab_schedule_list_schema
    def list(self, request, *args, **kwargs):
        """
        List lab schedules with pagination, filtering, and search.
        
        Results are ordered by date and start_time (upcoming schedules first).
        """
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

        # Fetch approved lab schedules for the given date (only active ones)
        approved_schedules = LabScheduleModel.objects.filter(
            date=target_date,
            is_active=True,
        ).values_list("start_time", "end_time")

        # Convert to list of tuples for the utility function
        occupied_slots = list(approved_schedules)

        # Calculate available slots using the utility generator
        available_slots = format_available_slots_for_api(occupied_slots)

        # Return all available slots
        if available_slots:
            serializer = self.get_serializer(available_slots, many=True)
            return ResponsePresenter.success_response(
                message=f"Lab availability for {date_str} retrieved successfully",
                data=serializer.data,
            )
        else:
            return ResponsePresenter.success_response(
                message=f"No available slots for {date_str}", data=[]
            )

    @lab_schedule_my_schedules_schema
    @action(detail=False, methods=["get"], url_path="me", permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get lab schedules related to the current user with filtering and pagination support.
        
        Includes schedules where user is:
        - Enrolled student or assigned TA in course sessions
        - Booker of room bookings  
        - Creator of lab allocations
        
        Results are ordered by date and start_time (upcoming schedules first).
        """
        from datetime import date
        
        user = request.user
        today = date.today()
        
        # Build query for user-related schedules from different source models
        user_schedules_query = Q()
        
        # 1. CourseSession schedules - where user is enrolled student or assigned TA
        from course.models import CourseSessionModel

        # Get course sessions where user is enrolled student or assigned TA
        user_course_sessions = CourseSessionModel.objects.filter(
            Q(course__students=user) |  # User is enrolled student
            Q(teaching_assistants=user)  # User is assigned TA to session
        ).values_list('id', flat=True)
        
        if user_course_sessions:
            course_session_ids = [str(session_id) for session_id in user_course_sessions]
            user_schedules_query |= Q(
                source_model="CourseSession",
                source_id__in=course_session_ids
            )
        
        # 2. RoomBooking schedules - where user is the booker
        from room_booking.models import RoomBookingModel
        
        user_room_bookings = RoomBookingModel.objects.filter(
            booker=user
        ).values_list('id', flat=True)
        
        if user_room_bookings:
            room_booking_ids = [str(booking_id) for booking_id in user_room_bookings]
            user_schedules_query |= Q(
                source_model="RoomBooking",
                source_id__in=room_booking_ids
            )
        
        # 3. LabAllocation schedules - where user is the creator
        from lab_allocation.models import LabAllocationModel
        
        user_lab_allocations = LabAllocationModel.objects.filter(
            created_by=user
        ).values_list('id', flat=True)
        
        if user_lab_allocations:
            lab_allocation_ids = [str(allocation_id) for allocation_id in user_lab_allocations]
            user_schedules_query |= Q(
                source_model="LabAllocation",
                source_id__in=lab_allocation_ids
            )
        
        # Start with user's schedules
        queryset = self.get_queryset().filter(user_schedules_query)
        
        # Apply filtering (date, type, etc.) using the same filter as list view
        queryset = self.filter_queryset(queryset)
        
        # Remove duplicates (ordering already handled in get_queryset)
        queryset = queryset.distinct()
        
        # Apply pagination like the list view
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Dynamic message based on filtering
        date_param = request.query_params.get('date')
        if date_param:
            message = f"Lab schedules for {date_param} retrieved successfully"
        else:
            message = "User's lab schedules retrieved successfully"
            
        return ResponsePresenter.success_response(
            message=message, 
            data=serializer.data
        )
