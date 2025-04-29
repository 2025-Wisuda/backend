from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from .models import LabSchedule
from .serializers import LabScheduleListSerializer, LabScheduleDetailSerializer
from django_filters.rest_framework import DjangoFilterBackend


class LabScheduleViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = [
        "activity_type",
        "schedule_date",
        "start_time",
        "end_time",
        "is_active",
    ]
    search_fields = ["activity_type", "activity_description"]

    def get_serializer_class(self):
        if self.action == "list":
            return LabScheduleListSerializer
        elif self.action == "retrieve":
            return LabScheduleDetailSerializer
        return LabScheduleListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return LabSchedule.objects.all()
        return LabSchedule.objects.filter(created_by=user, is_active=True)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (
            instance.created_by == request.user
            or request.user.is_staff
            or request.user.is_superuser
        ):
            raise PermissionDenied(
                "You do not have permission to update this schedule."
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (
            instance.created_by == request.user
            or request.user.is_staff
            or request.user.is_superuser
        ):
            raise PermissionDenied(
                "You do not have permission to delete this schedule."
            )
        return super().destroy(request, *args, **kwargs)
