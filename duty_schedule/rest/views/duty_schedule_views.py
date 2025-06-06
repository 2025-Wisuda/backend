"""
ViewSet for DutyScheduleModel (Bulk Duty Schedule Management).

Provides read-only API endpoints for duty schedule viewing and filtering.
This is a public API for lab schedule integration and display purposes.
"""

from datetime import date

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from core.enums.days_enum import DaysEnum  # Added import
from shared.presenter import ResponsePresenter

from ...models import DutyScheduleModel
from ..filters import DutyScheduleFilter
from ..schemas import duty_schedule_list_schema, duty_schedule_today_schema
from ..serializers import DutyScheduleSerializer, DutyScheduleTodaySerializer


class DutyScheduleViewSet(ListModelMixin, GenericViewSet):
    """
    Read-only ViewSet for Duty Schedule (Bulk) operations.

    Provides:
    - list: Get paginated list of duty schedules with filtering

    Note: Detail (retrieve) endpoint is disabled - only list is available.

    Filtering Options:
    - duty_days: Filter by day patterns (Senin, Selasa, etc.)
    - duty_start_date_from/to: Filter by start date range
    - is_generated: Filter by generation status

    Search Fields:
    - Assistant names (first_name, last_name, username)
    - Day patterns
    """

    # Only allow list functionality - detail endpoint is not available
    http_method_names = ["get", "head", "options"]

    filter_backends = [DjangoFilterBackend]
    filterset_class = DutyScheduleFilter

    serializer_class = DutyScheduleSerializer

    def get_queryset(self):
        """Get queryset with only active duty schedules (current and future schedules)."""
        from datetime import date

        today = date.today()

        return (
            DutyScheduleModel.objects.filter(
                is_active=True,
                duty_start_date__gte=today,  # Only current and future schedules
            )
            .prefetch_related("duty_assistants")
            .order_by("duty_start_date", "duty_start_time")
        )

    @duty_schedule_list_schema
    def list(self, request, *args, **kwargs):
        """List duty schedules with pagination, filtering, and search."""
        queryset = self.filter_queryset(self.get_queryset())

        # Group by duty_days to merge duplicates
        from collections import defaultdict

        grouped_data = defaultdict(list)

        # Process all schedules
        for schedule in queryset:
            serializer = self.get_serializer(schedule)
            duty_days = serializer.data["duty_days"]
            laboratory_assistants = serializer.data["laboratory_assistant"]

            # Add assistants to the group for this day
            grouped_data[duty_days].extend(laboratory_assistants)

        # Convert grouped data to final format
        result = []
        for duty_days, assistants in grouped_data.items():
            # Remove duplicates while preserving order
            seen = set()
            unique_assistants = []
            for assistant in assistants:
                # Create a unique key based on name and student_number
                key = (assistant["name"], assistant["student_number"])
                if key not in seen:
                    seen.add(key)
                    unique_assistants.append(assistant)

            result.append(
                {"duty_days": duty_days, "laboratory_assistant": unique_assistants}
            )

        # Sort by day order (optional - can be customized)
        day_order = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        result.sort(
            key=lambda x: (
                day_order.index(x["duty_days"]) if x["duty_days"] in day_order else 999
            )
        )

        return ResponsePresenter.success_response(
            message="Duty schedules retrieved successfully", data=result
        )

    @duty_schedule_today_schema
    @action(detail=False, methods=["get"], url_path="today")
    def today(self, request):
        """Get today's duty schedules with attendance status."""
        target_date = date.today()
        today_weekday = target_date.strftime("%A").upper()  # Get day name like 'MONDAY'

        # Map English day names to Indonesian using DaysEnum
        day_mapping = {day.name: day.value for day in DaysEnum}

        today_indonesian = day_mapping.get(today_weekday, today_weekday)

        # Filter schedules that should be active on target date and today's day
        queryset = DutyScheduleModel.objects.filter(
            is_active=True,
            duty_start_date__lte=target_date,  # Schedule has started
            duty_end_date__gte=target_date,  # Schedule hasn't ended
            duty_days__icontains=today_indonesian,  # Today is in duty days
        ).prefetch_related("duty_assistants")

        # Apply additional filters if any
        queryset = self.filter_queryset(queryset)

        # Group and merge duplicates like the general endpoint
        from collections import defaultdict

        grouped_assistants = []

        # Process all schedules for today
        for schedule in queryset:
            context = {"request": request, "date": target_date}
            serializer = DutyScheduleTodaySerializer(schedule, context=context)
            laboratory_assistants = serializer.data["laboratory_assistant"]
            grouped_assistants.extend(laboratory_assistants)

        # Remove duplicates while preserving order
        seen = set()
        unique_assistants = []
        for assistant in grouped_assistants:
            # Create a unique key based on name
            key = assistant["name"]
            if key not in seen:
                seen.add(key)
                unique_assistants.append(assistant)

        return ResponsePresenter.success_response(
            message=f"Today's duty schedules retrieved successfully for {today_indonesian}",
            data={"laboratory_assistant": unique_assistants},
        )
