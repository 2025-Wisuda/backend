"""
ViewSet for DutyScheduleModel (Bulk Duty Schedule Management).

Provides read-only API endpoints for duty schedule viewing and filtering.
This is a public API for lab schedule integration and display purposes.
"""

from datetime import date

from core.enums.days_enum import DaysEnum  # Added import
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet
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
    - days: Filter by day patterns (Senin, Selasa, etc.)
    - start_date_from/to: Filter by start date range
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
        """Get queryset with only active duty schedules."""
        return (
            DutyScheduleModel.objects.filter(
                is_active=True,
            )
            .prefetch_related("laboratory_assistants")
            .order_by("start_date", "start_time")
        )

    @duty_schedule_list_schema
    def list(self, request, *args, **kwargs):
        """List duty schedules with pagination, filtering, and search."""
        queryset = self.filter_queryset(self.get_queryset())

        # Serialize each schedule directly (no grouping needed with soft delete)
        result = []
        for schedule in queryset:
            serializer = self.get_serializer(schedule, context={'request': request})
            serialized_data = serializer.data
            result.append({
                "days": serialized_data["days"],
                "laboratory_assistant": serialized_data["assistants"]
            })

        # Sort by day order
        day_order = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        result.sort(
            key=lambda x: (
                day_order.index(x["days"]) if x["days"] in day_order else 999
            )
        )

        return ResponsePresenter.success_response(
            message="Duty schedules retrieved successfully", data=result
        )

    def _get_assistant_data_for_today(self, schedules_queryset, target_date):
        """Helper method to get assistant data with attendance status for today."""
        all_assistants = []
        
        for schedule in schedules_queryset:
            assistants = schedule.laboratory_assistants.all()
            
            for assistant in assistants:
                # Get assistant name
                first = assistant.first_name or ""
                last = assistant.last_name or ""
                
                if first and last:
                    name = f"{first} {last}"
                elif first:
                    name = first
                else:
                    name = assistant.username
                
                # Get attendance status
                try:
                    from ...models import DutyAttendanceModel
                    attendance = DutyAttendanceModel.objects.get(
                        duty_schedule=schedule,
                        laboratory_assistant=assistant,
                        date=target_date,
                        is_active=True,
                    )
                    status = attendance.status
                except DutyAttendanceModel.DoesNotExist:
                    # If no attendance record exists, use default scheduled status
                    from core.enums import AttendanceStatus
                    status = AttendanceStatus.SCHEDULED.value

                # Get avatar URL
                avatar_url = None
                if assistant.avatar:
                    avatar_url = self.request.build_absolute_uri(assistant.avatar.url)

                assistant_data = {
                    "name": name,
                    "student_number": getattr(assistant, "student_number", "") or assistant.username,
                    "status": status,
                    "avatar": avatar_url,
                }
                
                all_assistants.append(assistant_data)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_assistants = []
        for assistant in all_assistants:
            key = assistant["name"]
            if key not in seen:
                seen.add(key)
                unique_assistants.append(assistant)
        
        return unique_assistants

    @duty_schedule_today_schema
    @action(detail=False, methods=["get"], url_path="today")
    def today(self, request):
        """Get today's duty schedules with attendance status."""
        try:
            target_date = date.today()
            today_weekday = target_date.strftime("%A").upper()
            
            # Map English day names to Indonesian using DaysEnum
            day_mapping = {day.name: day.value for day in DaysEnum}
            today_indonesian = day_mapping.get(today_weekday, today_weekday)

            # Filter schedules that should be active on target date and today's day
            queryset = DutyScheduleModel.objects.filter(
                is_active=True,
                start_date__lte=target_date,
                end_date__gte=target_date,
                days__icontains=today_indonesian,
            ).prefetch_related("laboratory_assistants")

            if queryset.count() == 0:
                return ResponsePresenter.success_response(
                    message=f"No duty schedules found for {today_indonesian}",
                    data=[],
                )

            # Get assistant data using helper method
            unique_assistants = self._get_assistant_data_for_today(queryset, target_date)
            
            return ResponsePresenter.success_response(
                message=f"Today's duty schedules retrieved successfully for {today_indonesian}",
                data=unique_assistants,
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ResponsePresenter.internal_server_error_response(
                message=f"Error retrieving today's duty schedules: {str(e)}"
            )
