"""
DutyAttendanceViewSet - OTP + Face Recognition + Manual Override

Flow:
1. POST /validate-otp - OTP validation
2. POST /face-attendance - Face recognition (calls external service)
3. POST /manual-override - Manual status (fallback)
"""

import json
import logging
from datetime import date, datetime, time, timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from core.enums import AttendanceStatus, UserGroup
from django.core.exceptions import ValidationError
from django.db.models import Case, Count, IntegerField, Q, When
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from shared.presenter import ResponsePresenter
from shared.services.duty_otp_service import DutyOTPService
from shared.services.face_recognition_client import face_recognition_client
from shared.utils import require_groups

# Setup logger
logger = logging.getLogger(__name__)

from ...models import DutyAttendanceModel
from ..filters import DutyAttendanceFilter
from ..schemas import (
    duty_attendance_detail_schema,
    duty_attendance_list_schema,
    duty_attendance_manual_override_schema,
    duty_attendance_personal_schema,
    duty_attendance_statistics_schema,
    duty_otp_validation_schema,
)
from ..serializers import (
    DutyAttendanceDetailSerializer,
    DutyAttendanceListSerializer,
    DutyAttendanceManualOverrideSerializer,
    DutyAttendancePersonalSerializer,
    DutyAttendanceStatisticsSerializer,
    DutyOTPSerializer,
)


class DutyAttendanceViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    ViewSet for duty attendance operations.

    Provides:
    - list: Get paginated list of duty attendance records (admin use)
    - retrieve: Get details of a specific duty attendance record
    - me: Get personal attendance records (mobile/user use)
    - validate_otp: Custom action for OTP validation
    - face_attendance: Custom action for face recognition attendance
    - manual_override: Custom action for manual status override

    Note: Create, Update, Delete operations are disabled
    """

    http_method_names = ["get", "post", "patch", "head", "options"]

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = DutyAttendanceFilter
    ordering = ["-date", "-start_time"]
    search_fields = [
        "laboratory_assistant__first_name",
        "laboratory_assistant__last_name",
        "laboratory_assistant__username",
    ]

    def get_queryset(self):
        """Get attendance records accessible to the user."""

        user = self.request.user

        return DutyAttendanceModel.objects.select_related(
            "duty_schedule", "laboratory_assistant"
        ).filter(is_active=True)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return DutyAttendanceListSerializer
        elif self.action == "retrieve":
            return DutyAttendanceDetailSerializer
        elif self.action == "me":
            return DutyAttendancePersonalSerializer
        elif self.action == "validate_otp":
            return DutyOTPSerializer
        else:
            return DutyAttendanceDetailSerializer

    @duty_attendance_list_schema
    def list(self, request, *args, **kwargs):
        """Simple list of duty attendance records for admin use."""
        queryset = self.filter_queryset(self.get_queryset())

        date_filter = request.query_params.get("date")

        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                queryset = queryset.filter(date=filter_date)
            except ValueError:
                return ResponsePresenter.bad_request_response(
                    message="Invalid date format. Use YYYY-MM-DD"
                )
        else:
            today = timezone.localtime().date()
            queryset = queryset.filter(date__lte=today)

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

        serializer = self.get_serializer(instance)
        return ResponsePresenter.success_response(
            message="Attendance record retrieved successfully", data=serializer.data
        )

    @duty_otp_validation_schema
    @action(detail=False, methods=["post"], url_path="validate-otp")
    def validate_otp(self, request):
        """
        Step 1: Validate OTP before face recognition.

        """
        if request.user.group != UserGroup.LABORATORY_ASSISTANT.value:
            return ResponsePresenter.forbidden_response(
                message="Only laboratory assistants can validate OTP"
            )

        otp_code = request.data.get("otp_code")
        if not otp_code:
            return ResponsePresenter.bad_request_response(
                message="OTP code is required"
            )

        # Validate OTP
        is_valid, error_message = DutyOTPService.validate_otp(
            otp_code, str(request.user.id)
        )

        if not is_valid:
            return ResponsePresenter.bad_request_response(message=error_message)

        #  Mark OTP as used for this user bypass for now
        # DutyOTPService.mark_otp_used(otp_code, str(request.user.id), "otp_validation")

        # Update today's attendance records for face recognition unlock
        today = timezone.localtime().date()  # Use local time instead of UTC

        logger.info(f"OTP API Start - User: {request.user}, Today: {today}")

        attendance_records = DutyAttendanceModel.objects.filter(
            laboratory_assistant=request.user, date=today, is_active=True
        )

        logger.info(f"Found {attendance_records.count()} records for today")

        # Mark OTP validated on all today's records
        validated_count = 0
        for record in attendance_records:
            logger.debug(
                f"OTP Update - Record ID: {record.id}, User: {record.laboratory_assistant}, Date: {record.date}, Before: otp_validated_at = {record.otp_validated_at}"
            )

            record.mark_otp_validated()
            record.refresh_from_db()

            logger.debug(f"After: otp_validated_at = {record.otp_validated_at}")
            validated_count += 1

        return ResponsePresenter.success_response(
            message="OTP validated successfully. You can now use face recognition.",
            data={
                "valid": True,
                "expires_in_minutes": 5,
                "user_id": request.user.id,
                "username": request.user.username,
                "validated_records": validated_count,
            },
        )

    @duty_attendance_personal_schema
    @action(detail=False, methods=["get"], url_path="me")
    @require_groups(
        UserGroup.LABORATORY_ASSISTANT,
        error_message="Only laboratory assistants can access personal attendance records",
    )
    def me(self, request):
        """
        Get personal attendance records with automatic status update.

        This endpoint will:
        1. Automatically update expired attendance records for the user
        2. Return updated personal attendance data
        """
        # Auto-update expired attendance records for this user first
        self._update_expired_attendance_records_for_user(request.user)

        # Get query parameters
        date_filter = request.query_params.get("date")
        status_filter = request.query_params.get("status")

        # Base queryset - user's own records
        queryset = DutyAttendanceModel.objects.filter(
            laboratory_assistant=request.user, is_active=True
        ).select_related("duty_schedule")

        # Filter by date if provided
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                queryset = queryset.filter(date=filter_date)
            except ValueError:
                return ResponsePresenter.bad_request_response(
                    message="Invalid date format. Use YYYY-MM-DD"
                )
        else:
            # Default: today and past dates only (exclude future)
            today = timezone.localtime().date()
            queryset = queryset.filter(date__lte=today)

        # Filter by status if provided
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Order by date (newest first)
        queryset = queryset.order_by("-date", "-start_time")

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

    @duty_attendance_manual_override_schema
    @action(detail=True, methods=["patch"], url_path="manual-override")
    def manual_override(self, request, pk=None):
        """
        Manual clock in/out override.
        """
        attendance = self.get_object()
        user = request.user

        if (
            user.group
            not in [
                UserGroup.LABORATORY_HEAD.value,
                UserGroup.LABORATORY_TECHNICIAN.value,
            ]
            and attendance.laboratory_assistant != user
        ):
            return ResponsePresenter.forbidden_response(
                message="You can only override your own attendance or need admin privileges"
            )

        # Get request data
        action = request.data.get("action")

        if not action:
            return ResponsePresenter.bad_request_response(
                message="Action is required (clock_in or clock_out)"
            )

        if action not in ["clock_in", "clock_out"]:
            return ResponsePresenter.bad_request_response(
                message="Action must be 'clock_in' or 'clock_out'"
            )

        try:
            # Apply manual clock in/out
            if action == "clock_in":
                attendance.manual_clock_in(user=user)
            elif action == "clock_out":
                attendance.manual_clock_out(user=user)

            # Use proper DRF serializer instead of hardcoded dict
            response_data = {
                "attendance": attendance,
                "action": action,
                "status": attendance.status,
                "overridden_by": user.get_full_name(),
            }

            serializer = DutyAttendanceManualOverrideSerializer(response_data)
            return ResponsePresenter.success_response(
                message=f"Manual {action} successful",
                data=serializer.data,
            )

        except Exception as e:
            return ResponsePresenter.server_error_response(
                message=f"Manual {action} failed: {str(e)}"
            )

    @duty_attendance_statistics_schema
    @action(detail=False, methods=["get"], url_path="statistics")
    @require_groups(
        [UserGroup.LABORATORY_HEAD, UserGroup.LABORATORY_TECHNICIAN],
        error_message="Only admin users can access attendance statistics",
    )
    def statistics(self, request):
        """
        Get attendance statistics with automatic status update.

        This endpoint will:
        1. Automatically update expired attendance records
        2. Return updated statistics
        """
        # Auto-update expired attendance records first
        self._update_expired_attendance_records()

        # Get query parameters
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")
        assistant_id = request.query_params.get("assistant_id")

        # Parse dates
        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            else:
                # Default to 30 days ago
                start_date = timezone.localtime().date() - timedelta(days=30)

            if end_date_str:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            else:
                # Default to today
                end_date = timezone.localtime().date()

        except ValueError:
            return ResponsePresenter.bad_request_response(
                message="Invalid date format. Use YYYY-MM-DD"
            )

        # Base queryset
        queryset = DutyAttendanceModel.objects.filter(
            date__gte=start_date, date__lte=end_date, is_active=True
        ).select_related("laboratory_assistant")

        # Filter by assistant if specified
        if assistant_id:
            queryset = queryset.filter(laboratory_assistant_id=assistant_id)

        # Get daily trends data
        daily_trends = (
            queryset.values("date")
            .annotate(
                total=Count("id"),
                present=Count(
                    Case(
                        When(status=AttendanceStatus.PRESENT.value, then=1),
                        output_field=IntegerField(),
                    )
                ),
                absent=Count(
                    Case(
                        When(status=AttendanceStatus.ABSENT.value, then=1),
                        output_field=IntegerField(),
                    )
                ),
                late=Count(
                    Case(
                        When(status=AttendanceStatus.LATE.value, then=1),
                        output_field=IntegerField(),
                    )
                ),
            )
            .order_by("date")
        )

        # Get assistant performance data (if not filtered by specific assistant)
        assistant_stats = []
        if not assistant_id:
            assistant_stats = (
                queryset.values(
                    "laboratory_assistant__id",
                    "laboratory_assistant__first_name",
                    "laboratory_assistant__last_name",
                    "laboratory_assistant__username",
                )
                .annotate(
                    total_duties=Count("id"),
                    present_count=Count(
                        Case(
                            When(status=AttendanceStatus.PRESENT.value, then=1),
                            output_field=IntegerField(),
                        )
                    ),
                    absent_count=Count(
                        Case(
                            When(status=AttendanceStatus.ABSENT.value, then=1),
                            output_field=IntegerField(),
                        )
                    ),
                    late_count=Count(
                        Case(
                            When(status=AttendanceStatus.LATE.value, then=1),
                            output_field=IntegerField(),
                        )
                    ),
                )
                .order_by("-present_count")
            )

        # Use proper DRF serializer
        context_data = {
            "queryset": queryset,
            "start_date": start_date,
            "end_date": end_date,
            "assistant_id": assistant_id,
            "daily_trends": daily_trends,
            "assistant_stats": assistant_stats,
        }

        serializer = DutyAttendanceStatisticsSerializer(context_data)

        return ResponsePresenter.success_response(
            message="Attendance statistics retrieved successfully",
            data=serializer.data,
        )

    def _update_expired_attendance_records(self):
        """
        Automatically update expired attendance records.
        This method is called before returning statistics to ensure data is up-to-date.
        """
        from datetime import datetime, timedelta

        # Get records from last 30 days to avoid processing too many records
        end_date = timezone.localtime().date()
        start_date = end_date - timedelta(days=30)

        # Get scheduled attendance records in date range
        expired_records = DutyAttendanceModel.objects.filter(
            status=AttendanceStatus.SCHEDULED.value,
            is_active=True,
            date__gte=start_date,
            date__lte=end_date,
        )

        if not expired_records.exists():
            return

        # Process records
        updated_count = 0
        current_time = timezone.localtime()

        for attendance in expired_records:
            # Check if duty time has passed
            duty_end_datetime = datetime.combine(attendance.date, attendance.end_time)
            duty_end_datetime = timezone.make_aware(duty_end_datetime)

            if current_time > duty_end_datetime:
                # Update status to ABSENT
                attendance.status = AttendanceStatus.ABSENT.value
                attendance.save(update_fields=["status"])
                updated_count += 1

        # Log the update (optional)
        if updated_count > 0:
            logger.info(
                f"Auto-updated {updated_count} expired attendance records during statistics request"
            )

    def _update_expired_attendance_records_for_user(self, user):
        """
        Automatically update expired attendance records for a specific user.
        This method is called before returning personal attendance data.
        """
        from datetime import datetime, timedelta

        # Get records from last 30 days to avoid processing too many records
        end_date = timezone.localtime().date()
        start_date = end_date - timedelta(days=30)

        # Get scheduled attendance records in date range
        expired_records = DutyAttendanceModel.objects.filter(
            laboratory_assistant=user,
            status=AttendanceStatus.SCHEDULED.value,
            is_active=True,
            date__gte=start_date,
            date__lte=end_date,
        )

        if not expired_records.exists():
            return

        # Process records
        updated_count = 0
        current_time = timezone.localtime()

        for attendance in expired_records:
            # Check if duty time has passed
            duty_end_datetime = datetime.combine(attendance.date, attendance.end_time)
            duty_end_datetime = timezone.make_aware(duty_end_datetime)

            if current_time > duty_end_datetime:
                # Update status to ABSENT
                attendance.status = AttendanceStatus.ABSENT.value
                attendance.save(update_fields=["status"])
                updated_count += 1

        # Log the update (optional)
        if updated_count > 0:
            logger.info(
                f"Auto-updated {updated_count} expired attendance records for user {user.id}"
            )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _send_websocket_update(self, action, attendance):
        """Send real-time WebSocket update."""
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                # General attendance room
                async_to_sync(channel_layer.group_send)(
                    "duty_attendance",
                    {
                        "type": "attendance_update",
                        "action": action,
                        "attendance_id": str(attendance.id),
                        "user_id": str(attendance.laboratory_assistant.id),
                        "date": attendance.date.isoformat(),
                        "status": attendance.status,
                        "confidence": attendance.get_confidence_percentage(),
                        "timestamp": timezone.localtime().isoformat(),
                    },
                )

                # User-specific room
                async_to_sync(channel_layer.group_send)(
                    f"user_{attendance.laboratory_assistant.id}",
                    {
                        "type": "personal_attendance_update",
                        "action": action,
                        "attendance_id": str(attendance.id),
                        "status": attendance.status,
                        "confidence": attendance.get_confidence_percentage(),
                        "timestamp": timezone.localtime().isoformat(),
                    },
                )
        except Exception as e:
            # Log error but don't fail main operation
            logger.error(f"WebSocket update failed: {str(e)}")
