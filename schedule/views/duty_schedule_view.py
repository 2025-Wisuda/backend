from rest_framework import viewsets
from schedule.models import DutySchedule
from schedule.serializers import (
    DutyScheduleDetailSerializer,
    DutyScheduleListSerializer,
)


class DutyScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DutySchedule.objects.prefetch_related(
        "duty_dates", "teaching_assistants"
    ).filter(is_active=True)

    def get_serializer_class(self):
        if "retrieve":
            return DutyScheduleDetailSerializer
        return DutyScheduleListSerializer
