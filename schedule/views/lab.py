from datetime import datetime
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from schedule.models import LabSchedule
from schedule.serializers import LabScheduleDetailSerializer, LabScheduleListSerializer
from django_filters import FilterSet, DateFilter


class LabScheduleFilter(FilterSet):
    start_date = DateFilter(field_name="schedule_date", lookup_expr="gte")
    end_date = DateFilter(field_name="schedule_date", lookup_expr="lte")

    class Meta:
        model = LabSchedule
        fields = [
            "activity_type",
            "schedule_date",
            "created_by",
            "approval_status",
            "start_date",
            "end_date",
        ]


class LabScheduleViewSet(viewsets.ModelViewSet):
    queryset = LabSchedule.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LabScheduleFilter
    search_fields = ["activity_type", "activity_description"]
    ordering_fields = ["schedule_date", "created_by", "approval_status"]
    ordering = ["schedule_date"]

    def get_serializer_class(self):
        if self.action in ["retrieve", "create", "update", "partial_update"]:
            return LabScheduleDetailSerializer
        return LabScheduleListSerializer

    def perform_create(self, serializer):
        if self.request.user.is_staff or self.request.user.is_superuser:
            approval_status = "diterima"
            approved_by = self.request.user
            approval_time = datetime.now()
        else:
            approval_status = "menunggu"
            approved_by = None
            approval_time = None

        serializer.save(
            created_by=self.request.user,
            approval_status=approval_status,
            approved_by=approved_by,
            approval_time=approval_time,
        )

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (instance.created_by == request.user):
            raise PermissionDenied("You do not have permission to update this schedule.")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (instance.created_by == request.user):
            raise PermissionDenied("You do not have permission to update this schedule.")
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (
            instance.created_by == request.user
            or request.user.is_staff
            or request.user.is_superuser
        ):
            raise PermissionDenied("You do not have permission to delete this schedule.")
        return super().destroy(request, *args, **kwargs)
