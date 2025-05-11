from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    DateFilter,
    CharFilter,
)
from course.models import Course
from course.serializers import (
    CourseListSerializer,
    CourseDetailSerializer,
    CourseEnrollKeySerializer,
)


class CourseFilter(FilterSet):
    start_date = DateFilter(field_name="start_date", lookup_expr="gte")
    end_date = DateFilter(field_name="end_date", lookup_expr="lte")
    title = CharFilter(field_name="title", lookup_expr="icontains")
    description = CharFilter(field_name="description", lookup_expr="icontains")

    class Meta:
        model = Course
        fields = ["title", "description", "start_date", "end_date"]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.prefetch_related(
        "students",
        "teaching_assistants",
        "sessions",
    ).filter(is_active=True)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ["title", "description"]
    ordering_fields = ["start_date", "end_date"]
    ordering = ["start_date"]

    def get_serializer_class(self):
        if self.action == "enroll":
            return CourseEnrollKeySerializer
        if self.action in ["retrieve", "create", "partial_update", "update"]:
            return CourseDetailSerializer
        return CourseListSerializer

    def perform_create(self, serializer):
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            raise PermissionDenied("You do not have permission to create a course.")
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    def is_staff_teaching_assistant(self, user, course):
        return course.teaching_assistants.filter(id=user.id).exists() and user.is_staff

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not self.is_staff_teaching_assistant(request.user, instance):
            raise PermissionDenied("You do not have permission to update this course.")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not self.is_staff_teaching_assistant(request.user, instance):
            raise PermissionDenied("You do not have permission to update this course.")
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (instance.created_by == request.user or request.user.is_superuser):
            raise PermissionDenied("You do not have permission to delete this course.")
        self.perform_destroy(instance)
        return Response(
            {"detail": "Course successfully deleted."}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"], url_path="enroll")
    def enroll(self, request, pk=None):
        course = self.get_object()

        if request.user in course.students.all():
            return Response(
                {"detail": "You are already enrolled as a student."},
                status=status.HTTP_200_OK,
            )
        if request.user in course.teaching_assistants.all():
            return Response(
                {"detail": "You are already a teaching assistant in this course."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CourseEnrollKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["enroll_key"] != course.enroll_key:
            return Response(
                {"detail": "Invalid enroll key."}, status=status.HTTP_400_BAD_REQUEST
            )

        course.add_student(request.user)
        return Response(
            {"detail": "Successfully enrolled as student."}, status=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        course = self.get_object()
        show_sessions = (
            not course.enroll_key
            or request.user in course.students.all()
            or request.user in course.teaching_assistants.all()
            or request.user.is_superuser
        )
        serializer = CourseDetailSerializer(
            course,
            context={**self.get_serializer_context(), "show_sessions": show_sessions},
        )
        return Response(serializer.data)
