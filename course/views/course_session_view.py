from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter
from course.models import CourseSession
from course.serializers import (
    CourseSessionListSerializer,
    CourseSessionDetailSerializer,
)
from schedule.models import LabSchedule
from schedule.validators import validate_lab_schedule_fields

from django.utils import timezone  

class CourseSessionFilter(FilterSet):
    title = CharFilter(field_name="title", lookup_expr="icontains")
    status = CharFilter(field_name="status", lookup_expr="exact")

    class Meta:
        model = CourseSession
        fields = ["course", "session_date", "status", "title"]


class CourseSessionViewSet(viewsets.ModelViewSet):
    queryset = CourseSession.objects.prefetch_related(
        "course", "teaching_assistants", "lab_schedule"
    ).filter(is_active=True)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CourseSessionFilter
    search_fields = ["title", "course__name"]
    ordering_fields = ["session_date"]
    ordering = ["session_date", "start_time"]

    def get_serializer_class(self):
        if self.action in ["retrieve", "create", "update", "partial_update"]:
            return CourseSessionDetailSerializer
        return CourseSessionListSerializer

    def is_teaching_assistant(self, user, course):
        return course.teaching_assistants.filter(id=user.id).exists()

    def perform_create(self, serializer):
        course = serializer.validated_data["course"]
        if not self.is_teaching_assistant(self.request.user, course):
            raise PermissionDenied(
                "Only teaching assistants of the course can create a session."
            )

        course_session = serializer.save(created_by=self.request.user)

        lab_schedule_data = {
            "activity_type": LabSchedule.ActivityType.PRACTICUM,
            "activity_description": course_session.title,
            "schedule_date": course_session.session_date,
            "start_time": course_session.start_time,
            "end_time": course_session.end_time,
            "created_by": self.request.user,
        }

        if self.request.user.is_staff or self.request.user.is_superuser:
            if course_session.session_date and course_session.start_time and course_session.end_time:
                lab_schedule_data.update(
                    {
                        "approval_status": LabSchedule.ApprovalStatus.APPROVED,
                        "approved_by": self.request.user,
                        "approval_time": timezone.now(),
                    }
                )

        validate_lab_schedule_fields(lab_schedule_data)
        lab_schedule = LabSchedule.objects.create(**lab_schedule_data)
        course_session.lab_schedule = lab_schedule
        course_session.save()


    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
        if instance.lab_schedule:
            instance.lab_schedule.is_active = False
            instance.lab_schedule.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if (
            not self.is_teaching_assistant(request.user, instance.course)
            and not request.user.is_superuser
        ):
            raise PermissionDenied(
                "Only teaching assistants or superusers can fully update the session."
            )

        response = super().update(request, *args, **kwargs)
        updated_instance = self.get_object()

        if updated_instance.lab_schedule:
            updated_instance.lab_schedule.activity_description = updated_instance.title
            updated_instance.lab_schedule.schedule_date = updated_instance.session_date
            updated_instance.lab_schedule.start_time = updated_instance.start_time
            updated_instance.lab_schedule.end_time = updated_instance.end_time
            updated_instance.lab_schedule.save()

        return response

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        allowed_fields = {"session_date", "start_time", "end_time"}
        request_fields = set(request.data.keys())

        if (
            not self.is_teaching_assistant(request.user, instance.course)
            and not request.user.is_superuser
        ):
            if not request_fields.issubset(allowed_fields):
                raise PermissionDenied(
                    "You can only update the date and time fields for this session."
                )

            if (
                (instance.session_date and "session_date" in request.data)
                or (instance.start_time and "start_time" in request.data)
                or (instance.end_time and "end_time" in request.data)
            ):
                raise PermissionDenied(
                    "The date and time cannot be changed once they are set."
                )

        response = super().partial_update(request, *args, **kwargs)
        updated_instance = self.get_object()

        if updated_instance.lab_schedule:
            if "session_date" in request.data:
                updated_instance.lab_schedule.schedule_date = (
                    updated_instance.session_date
                )
            if "start_time" in request.data:
                updated_instance.lab_schedule.start_time = updated_instance.start_time
            if "end_time" in request.data:
                updated_instance.lab_schedule.end_time = updated_instance.end_time
            updated_instance.lab_schedule.save()

        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (instance.created_by == request.user or request.user.is_superuser):
            raise PermissionDenied("You do not have permission to delete this course.")
        self.perform_destroy(instance)
        return Response(
            {"detail": "Course successfully deleted."}, status=status.HTTP_200_OK
        )
