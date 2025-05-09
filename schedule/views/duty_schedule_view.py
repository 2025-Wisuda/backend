from rest_framework import viewsets
from schedule.models import DutySchedule
from schedule.serializers import DutyScheduleDetailSerializer, DutyScheduleListSerializer
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter

class DutyScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DutySchedule.objects.prefetch_related(
        "duty_dates", "teaching_assistants"
    ).filter(is_active=True)

    filter_backends = [DjangoFilterBackend]
    
    filterset_fields = {
        "days": ["iexact"],
    }

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DutyScheduleDetailSerializer
        return DutyScheduleListSerializer
