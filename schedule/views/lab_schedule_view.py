from datetime import datetime, time, timedelta
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    DateFilter,
    CharFilter,
)
from schedule.models import LabSchedule
from schedule.serializers import LabScheduleDetailSerializer, LabScheduleListSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter


class LabScheduleFilter(FilterSet):
    start_date = DateFilter(field_name="schedule_date", lookup_expr="gte")
    end_date = DateFilter(field_name="schedule_date", lookup_expr="lte")
    name = CharFilter(field_name="name", lookup_expr="icontains")
    description = CharFilter(field_name="description", lookup_expr="icontains")

    class Meta:
        model = LabSchedule
        fields = [
            "start_date",
            "end_date",
            "activity_type",
            "activity_description",
            "schedule_date",
            "approval_status",
        ]


class LabScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LabSchedule.objects.prefetch_related(
        "created_by",
        "approved_by",
    ).filter(is_active=True)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LabScheduleFilter
    search_fields = ["activity_type", "activity_description"]
    ordering_fields = ["schedule_date", "start_date", "end_date"]
    ordering = ["schedule_date"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LabScheduleDetailSerializer
        return LabScheduleListSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="date",
                type=str,
                required=True,
                description="Date in YYYY-MM-DD format",
            ),
        ]
    )
    @action(detail=False, methods=["get"])
    def availability(self, request, *args, **kwargs):
        date_str = request.query_params.get("date")
        if not date_str:
            return Response({"error": "Date is required."}, status=400)

        try:
            schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."}, status=400
            )

        start_of_day = time(7, 30)
        end_of_day = time(18, 0)
        durations = [60, 90, 120]
        step = 30

        start_dt = datetime.combine(schedule_date, start_of_day)
        end_dt = datetime.combine(schedule_date, end_of_day)

        available_slots = []
        booked_slots = []
        total_available_minutes = 0
        total_booked_minutes = 0

        current = start_dt
        while current + timedelta(minutes=step) <= end_dt:
            for duration in durations:
                slot_end = current + timedelta(minutes=duration)
                if slot_end > end_dt:
                    continue

                start_t = current.time()
                end_t = slot_end.time()

                is_booked = LabSchedule.objects.filter(
                    schedule_date=schedule_date,
                    start_time__lt=end_t,
                    end_time__gt=start_t,
                    is_active=True,
                ).exists()

                slot_data = {
                    "start_time": start_t.strftime("%H:%M"),
                    "end_time": end_t.strftime("%H:%M"),
                }

                if is_booked:
                    booked_slots.append(slot_data)
                    total_booked_minutes += duration
                else:
                    available_slots.append(slot_data)
                    total_available_minutes += duration

            current += timedelta(minutes=step)

        total_available_minutes = min(total_available_minutes, 10 * 60 + 30)

        return Response(
            {
                "total_hours_available": round(total_available_minutes / 60, 2),
                "total_hours_booked": round(total_booked_minutes / 60, 2),
                "available_slots": available_slots,
                "booked_slots": booked_slots,
            }
        )
