from datetime import datetime
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from .models import LabSchedule
from .serializers import (
    LabScheduleListSerializer,
    LabScheduleDetailSerializer,
    LabScheduleApprovalSerializer,
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, F, ExpressionWrapper, DurationField
from django.db.models.functions import ExtractDay, ExtractMonth, ExtractYear
from rest_framework.views import APIView
from django.http import JsonResponse
from .models import LabSchedule
from datetime import datetime


class LabScheduleViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = [
        "activity_type",
        "schedule_date",
        "start_time",
        "end_time",
        "created_by",
        "approval_status",
    ]
    search_fields = ["activity_type", "activity_description"]

    def get_serializer_class(self):
        if self.action in ["retrieve", "create", "update", "partial_update"]:
            return LabScheduleDetailSerializer
        return LabScheduleListSerializer

    def get_queryset(self):
        return LabSchedule.objects.filter(is_active=True)

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
            raise PermissionDenied(
                "You do not have permission to update this schedule."
            )
        response = super().update(request, *args, **kwargs)
        return response

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (instance.created_by == request.user):
            raise PermissionDenied(
                "You do not have permission to update this schedule."
            )
        response = super().partial_update(request, *args, **kwargs)
        return response

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


class LabScheduleApprovalViewSet(viewsets.ModelViewSet):
    queryset = LabSchedule.objects.all()
    serializer_class = LabScheduleApprovalSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if not request.user.is_staff and not request.user.is_superuser:
            raise PermissionDenied(
                "You do not have permission to update the approval status."
            )

        status = request.data.get("approval_status")
        if status not in ["menunggu"]:
            raise PermissionDenied("Invalid approval status.")

        if status == "diterima":
            instance.approved_by = request.user
            instance.approval_time = datetime.now()
        else:
            instance.approved_by = None
            instance.approval_time = None

        instance.approval_status = status
        instance.save()

        return super().update(request, *args, **kwargs)
