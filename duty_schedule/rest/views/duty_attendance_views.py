"""
ViewSets for DutyAttendanceModel (Individual Attendance Tracking).

Mobile-first API with manual clock in/out functionality.
Prefix: duty-schedule/my-duties/
"""

import json
from datetime import date, datetime, time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from core.enums import UserGroup
from core.enums.clock_method_enum import ClockMethod
from shared.presenter import ResponsePresenter
from shared.services.duty_otp_service import DutyOTPService
from shared.utils.permission_config_utils import require_groups, require_owner_or_groups

from ...models import DutyAttendanceModel
from ..filters import DutyAttendanceFilter
from ..schemas import (
    duty_attendance_clock_in_schema,
    duty_attendance_clock_out_schema,
    duty_attendance_detail_schema,
    duty_attendance_list_schema,
    duty_attendance_personal_schema,
    duty_otp_validation_schema,
)
from ..serializers import (
    DutyAttendanceClockInSerializer,
    DutyAttendanceClockOutSerializer,
    DutyAttendanceDetailSerializer,
    DutyAttendanceListSerializer,
    DutyAttendancePersonalSerializer,
    DutyOTPSerializer,
)


class DutyAttendanceViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    ViewSet for duty attendance operations.

    Provides:
    - history: Get paginated list of duty attendance records (admin use)
    - history/me: Get personal attendance records (user use)
    - clock-in: Simple POST to clock in
    - clock-out: Simple POST to clock out
    - validate_otp: Custom action for OTP validation

    Simple manual attendance system without face recognition complexity.
    """

    http_method_names = ["get", "post", "head", "options"]

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = DutyAttendanceFilter
    ordering = ["-duty_date", "-duty_start_time"]
    search_fields = [
        "duty_assistant__first_name",
        "duty_assistant__last_name",
        "duty_assistant__username",
    ]

    def get_queryset(self):
        """Get attendance records accessible to the user."""

        user = self.request.user

        return DutyAttendanceModel.objects.select_related(
            "duty_schedule", "duty_assistant"
        ).filter(is_active=True)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "history":
            return DutyAttendanceListSerializer
        elif self.action == "retrieve":
            return DutyAttendanceDetailSerializer
        elif self.action == "me":
            return DutyAttendancePersonalSerializer
        elif self.action == "validate_otp":
            return DutyOTPSerializer
        elif self.action == "clock_in":
            return DutyAttendanceClockInSerializer
        elif self.action == "clock_out":
            return DutyAttendanceClockOutSerializer
        else:
            return DutyAttendanceDetailSerializer

    @duty_attendance_list_schema
    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request, *args, **kwargs):
        """Simple list of duty attendance records for admin use."""
        queryset = self.filter_queryset(self.get_queryset())

        # Simple listing without complex annotations
        # Mobile apps should use /history/me endpoint instead
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return ResponsePresenter.success_response(
            message="Duty attendance records retrieved successfully",
            data=serializer.data,
        )

    @duty_attendance_detail_schema
    def retrieve(self, request, *args, **kwargs):
        """Retrieve detailed attendance record for a specific duty."""
        instance = self.get_object()

        # Check if user has permission to view this record
        if (
            request.user.group != UserGroup.LABORATORY_HEAD.value
            and instance.duty_assistant != request.user
        ):
            return ResponsePresenter.forbidden_response(
                message="You do not have permission to view this attendance record"
            )

        serializer = self.get_serializer(instance)
        return ResponsePresenter.success_response(
            message="Attendance record retrieved successfully", data=serializer.data
        )

    @duty_otp_validation_schema
    @action(detail=False, methods=["post"], url_path="validate-otp")
    @require_groups(
        UserGroup.LABORATORY_ASSISTANT,
        error_message="Only laboratory assistants can validate OTP codes",
    )
    def validate_otp(self, request):
        """Validate OTP before allowing clock operations."""
        serializer = DutyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp_code = serializer.validated_data["otp_code"]
        user_id = request.user.id

        # Validate OTP using service
        otp_service = DutyOTPService()
        is_valid = otp_service.validate_otp(otp_code, user_id)

        if not is_valid:
            return ResponsePresenter.bad_request_response(
                message="Invalid or expired OTP code"
            )

        return ResponsePresenter.success_response(
            message="OTP validated successfully. You can now clock in/out.",
            data={"otp_valid": True, "expires_in_minutes": 5},
        )

    @duty_attendance_clock_in_schema
    @action(detail=True, methods=["post"], url_path="clock-in")
    @require_owner_or_groups(
        [UserGroup.LABORATORY_HEAD, UserGroup.LABORATORY_TECHNICIAN],
        error_message="You can only clock in to your own duties or need admin privileges",
    )
    def clock_in(self, request, pk=None):
        """
        Simple POST to clock in - manual attendance.
        """
        attendance = self.get_object()
        user = request.user

        # Basic permission check
        if (
            user.group != UserGroup.ADMINISTRATOR.value
            and attendance.duty_assistant != user
        ):
            return ResponsePresenter.forbidden_response(
                message="You can only clock in to your own duties"
            )

        # Check if already clocked in
        if attendance.clock_in_time:
            return ResponsePresenter.bad_request_response(
                message="Already clocked in for this duty"
            )

        # Validate request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Simple clock in - just set time and method
            attendance.clock_in_time = timezone.now()
            attendance.clock_in_method = ClockMethod.MANUAL.value

            # Optional location data
            if serializer.validated_data.get(
                "latitude"
            ) and serializer.validated_data.get("longitude"):
                attendance.clock_in_location = {
                    "latitude": serializer.validated_data["latitude"],
                    "longitude": serializer.validated_data["longitude"],
                }

            # Calculate status
            attendance.calculate_status()
            attendance.save()

            # WebSocket update
            self._send_websocket_update("clock_in", attendance)

            return ResponsePresenter.success_response(
                message="Clock in successful",
                data=DutyAttendanceDetailSerializer(attendance).data,
            )

        except Exception as e:
            return ResponsePresenter.server_error_response(
                message=f"Clock in failed: {str(e)}"
            )

    @duty_attendance_clock_out_schema
    @action(detail=True, methods=["post"], url_path="clock-out")
    @require_owner_or_groups(
        [UserGroup.LABORATORY_HEAD, UserGroup.LABORATORY_TECHNICIAN],
        error_message="You can only clock out from your own duties or need admin privileges",
    )
    def clock_out(self, request, pk=None):
        """
        Simple POST to clock out - manual attendance.
        """
        attendance = self.get_object()
        user = request.user

        # Basic permission check
        if (
            user.group != UserGroup.ADMINISTRATOR.value
            and attendance.duty_assistant != user
        ):
            return ResponsePresenter.forbidden_response(
                message="You can only clock out from your own duties"
            )

        # Check if clocked in first
        if not attendance.clock_in_time:
            return ResponsePresenter.bad_request_response(
                message="Must clock in before clocking out"
            )

        # Check if already clocked out
        if attendance.clock_out_time:
            return ResponsePresenter.bad_request_response(
                message="Already clocked out for this duty"
            )

        # Validate request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Simple clock out - just set time and method
            attendance.clock_out_time = timezone.now()
            attendance.clock_out_method = ClockMethod.MANUAL.value

            # Optional location data
            if serializer.validated_data.get(
                "latitude"
            ) and serializer.validated_data.get("longitude"):
                attendance.clock_out_location = {
                    "latitude": serializer.validated_data["latitude"],
                    "longitude": serializer.validated_data["longitude"],
                }

            # Calculate status
            attendance.calculate_status()
            attendance.save()

            # WebSocket update
            self._send_websocket_update("clock_out", attendance)

            return ResponsePresenter.success_response(
                message="Clock out successful",
                data=DutyAttendanceDetailSerializer(attendance).data,
            )

        except Exception as e:
            return ResponsePresenter.server_error_response(
                message=f"Clock out failed: {str(e)}"
            )

    @duty_attendance_personal_schema
    @action(detail=False, methods=["get"], url_path="history/me")
    @require_groups(
        UserGroup.LABORATORY_ASSISTANT,
        error_message="Only laboratory assistants can access personal attendance records",
    )
    def me(self, request):
        """Get simplified personal attendance records for the authenticated user (today and past only)."""
        user = request.user
        today = timezone.now().date()

        # Simple query - only user's own records for today and past dates
        # Future dates are excluded since attendance hasn't been done yet
        queryset = (
            DutyAttendanceModel.objects.select_related("duty_schedule")
            .filter(
                duty_assistant=user,
                is_active=True,
                duty_date__lte=today,  # Only today and past dates
            )
            .order_by("-duty_date")
        )

        # Apply basic filtering if provided
        duty_date = request.query_params.get("duty_date")
        if duty_date:
            try:
                duty_date = datetime.strptime(duty_date, "%Y-%m-%d").date()
                # Still respect the today-and-past rule even with specific date filter
                if duty_date <= today:
                    queryset = queryset.filter(duty_date=duty_date)
                else:
                    # Return empty result for future dates
                    queryset = queryset.none()
            except ValueError:
                return ResponsePresenter.bad_request_response(
                    message="Invalid duty_date format. Use YYYY-MM-DD"
                )

        attendance_status = request.query_params.get("attendance_status")
        if attendance_status:
            queryset = queryset.filter(attendance_status=attendance_status)

        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return ResponsePresenter.success_response(
            message="Personal attendance records retrieved successfully",
            data=serializer.data,
        )
