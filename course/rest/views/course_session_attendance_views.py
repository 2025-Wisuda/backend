"""
CourseSessionAttendanceViewSet - Face Recognition + Manual Override

Flow:
1. WebSocket /ws/course-attendance/ - Face recognition (1:1 student validation)
2. PATCH /manual-override - Manual status (simple fallback)

No OTP required - only TAs can mark attendance for students.
"""

import logging
from datetime import datetime, timedelta

from core.enums import AttendanceStatus, UserGroup
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from shared.presenter import ResponsePresenter
from shared.utils import require_groups

# Setup logger
logger = logging.getLogger(__name__)

from ...models import CourseSessionAttendanceModel
from ..filters import CourseSessionAttendanceFilter
from ..schemas import (
    course_session_attendance_detail_schema,
    course_session_attendance_list_schema,
    course_session_attendance_manual_override_schema,
    course_session_attendance_personal_schema,
)
from ..serializers import (
    CourseSessionAttendanceDetailSerializer,
    CourseSessionAttendanceListSerializer,
    CourseSessionAttendanceManualOverrideSerializer,
    CourseSessionAttendancePersonalSerializer,
)


class CourseSessionAttendanceViewSet(
    ListModelMixin, RetrieveModelMixin, GenericViewSet
):
    """
    ViewSet for course session attendance operations.

    Provides:
    - list: Get paginated list of attendance records for course session
    - retrieve: Get details of a specific attendance record
    - me: Get personal attendance records (student use)
    - manual_override: Manual status override (TA only, simple)

    Face recognition handled via WebSocket: /ws/course-attendance/
    """

    http_method_names = ["get", "patch", "head", "options"]

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CourseSessionAttendanceFilter
    search_fields = [
        "student__first_name",
        "student__last_name",
        "student__username",
        "student__student_number",
    ]

    def get_queryset(self):
        """Get attendance records accessible to the user."""
        user = self.request.user

        # Get course_id and session_id from URL kwargs
        course_id = self.kwargs.get("course_pk")
        session_id = self.kwargs.get("session_pk")

        queryset = CourseSessionAttendanceModel.objects.select_related(
            "course_session", "student", "course_session__course"
        ).filter(is_active=True)

        # Filter by course and session if provided
        if course_id:
            queryset = queryset.filter(course_session__course_id=course_id)
        if session_id:
            queryset = queryset.filter(course_session_id=session_id)

        # Permission-based filtering
        if user.group == UserGroup.STUDENT.value:
            # Students can only see their own attendance
            queryset = queryset.filter(student=user)
        elif user.group == UserGroup.LABORATORY_ASSISTANT.value:
            # TAs can see attendance for courses they're assigned to
            queryset = queryset.filter(course_session__teaching_assistants=user)
        elif user.group in [UserGroup.LABORATORY_HEAD.value, UserGroup.LECTURER.value]:
            # Admins can see all attendance
            pass
        else:
            # Other users see nothing
            queryset = queryset.none()

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return CourseSessionAttendanceListSerializer
        elif self.action == "retrieve":
            return CourseSessionAttendanceDetailSerializer
        elif self.action == "me":
            return CourseSessionAttendancePersonalSerializer
        elif self.action == "manual_override":
            return CourseSessionAttendanceManualOverrideSerializer
        else:
            return CourseSessionAttendanceDetailSerializer

    @course_session_attendance_list_schema
    def list(self, request, *args, **kwargs):
        """List attendance records for course session with auto status update."""
        # Auto-update expired attendance records first
        self._update_expired_attendance_records()

        queryset = self.filter_queryset(self.get_queryset())

        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return ResponsePresenter.success_response(
            message="Course session attendance records retrieved successfully",
            data=serializer.data,
        )

    @course_session_attendance_detail_schema
    def retrieve(self, request, *args, **kwargs):
        """Retrieve detailed attendance record."""
        instance = self.get_object()

        # Check if user has permission to view this record
        user = request.user
        if user.group == UserGroup.STUDENT.value and instance.student != user:
            return ResponsePresenter.forbidden_response(
                message="You can only view your own attendance records"
            )
        elif (
            user.group == UserGroup.LABORATORY_ASSISTANT.value
            and not instance.course_session.teaching_assistants.filter(
                id=user.id
            ).exists()
        ):
            return ResponsePresenter.forbidden_response(
                message="You can only view attendance for courses you're assigned to"
            )

        serializer = self.get_serializer(instance)
        return ResponsePresenter.success_response(
            message="Attendance record retrieved successfully",
            data=serializer.data,
        )

    @course_session_attendance_personal_schema
    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request, course_pk=None, session_pk=None, *args, **kwargs):
        """Get personal attendance record for a specific course session (single object)."""
        if not course_pk or not session_pk:
            return ResponsePresenter.bad_request_response(
                message="course_pk and session_pk are required in path"
            )
        try:
            attendance = CourseSessionAttendanceModel.objects.select_related(
                "course_session", "course_session__course"
            ).get(
                student=request.user,
                course_session__course_id=course_pk,
                course_session_id=session_pk,
                is_active=True,
            )
        except CourseSessionAttendanceModel.DoesNotExist:
            return ResponsePresenter.success_response(
                message="Attendance record not found.",
                data=None,
            )

        serializer = self.get_serializer(attendance)
        return ResponsePresenter.success_response(
            message="Personal attendance record retrieved successfully",
            data=serializer.data,
        )

    @course_session_attendance_manual_override_schema
    @action(detail=True, methods=["patch"], url_path="manual-override")
    @require_groups(
        UserGroup.LABORATORY_ASSISTANT,
        error_message="Only laboratory assistants can manually mark attendance",
    )
    def manual_override(self, request, pk=None):
        """Simple manual attendance override - no parameters needed."""
        attendance = self.get_object()
        user = request.user

        # Check if TA is assigned to this course session
        if not attendance.course_session.teaching_assistants.filter(
            id=user.id
        ).exists():
            return ResponsePresenter.forbidden_response(
                message="You are not assigned as TA to this course session"
            )

        # Check if attendance can be marked
        if not attendance.can_mark_attendance():
            return ResponsePresenter.bad_request_response(
                message="Attendance already marked for this student"
            )

        try:
            # Mark attendance as present (simple override)
            attendance.manual_mark_attendance(user=user)

            # Use proper DRF serializer
            response_data = {
                "attendance": attendance,
                "status": attendance.status,
                "marked_by": user.get_full_name(),
                "marked_at": attendance.marked_at,
            }

            serializer = CourseSessionAttendanceManualOverrideSerializer(response_data)
            return ResponsePresenter.success_response(
                message="Manual attendance marked successfully",
                data=serializer.data,
            )

        except Exception as e:
            logger.error(f"Manual override failed: {str(e)}")
            return ResponsePresenter.server_error_response(
                message=f"Manual attendance marking failed: {str(e)}"
            )

    def _update_expired_attendance_records(self):
        """Update expired attendance records for all users."""
        try:
            # Get all active attendance records that are expired
            expired_records = CourseSessionAttendanceModel.objects.filter(
                is_active=True,
                status=AttendanceStatus.SCHEDULED.value,
                course_session__date__lt=timezone.localtime().date(),
            )

            updated_count = 0
            for record in expired_records:
                record.status = AttendanceStatus.ABSENT.value
                record.save(update_fields=["status", "updated_at"])
                updated_count += 1

            if updated_count > 0:
                logger.info(
                    f"Updated {updated_count} expired course session attendance records"
                )

        except Exception as e:
            logger.error(f"Error updating expired attendance records: {str(e)}")

    def _update_expired_attendance_records_for_user(self, user):
        """Update expired attendance records for specific user."""
        try:
            # Get user's expired attendance records
            expired_records = CourseSessionAttendanceModel.objects.filter(
                student=user,
                is_active=True,
                status=AttendanceStatus.SCHEDULED.value,
                course_session__date__lt=timezone.localtime().date(),
            )

            updated_count = 0
            for record in expired_records:
                record.status = AttendanceStatus.ABSENT.value
                record.save(update_fields=["status", "updated_at"])
                updated_count += 1

            if updated_count > 0:
                logger.info(
                    f"Updated {updated_count} expired attendance records for user {user.username}"
                )

        except Exception as e:
            logger.error(
                f"Error updating expired attendance records for user {user.username}: {str(e)}"
            )
