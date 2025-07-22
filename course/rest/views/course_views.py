"""
ViewSet classes for course API endpoints.

This module provides ViewSet classes for course models
following the established patterns in the project.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from shared.presenter import ResponsePresenter
from shared.utils.permission_config_utils import laboratory_assistant_only

from ...models import CourseModel
from ..filters import CourseFilter
from ..schemas import (
    course_create_schema,
    course_destroy_schema,
    course_detail_schema,
    course_enroll_schema,
    course_list_schema,
    course_my_courses_schema,
    course_update_schema,
)
from ..serializers import (
    CourseDetailSerializer,
    CourseEnrollSerializer,
    CourseListSerializer,
)


class CourseViewSet(ModelViewSet):
    """
    ViewSet for course management.

    Provides CRUD operations for courses with enrollment functionality.
    Follows established patterns with proper permissions and filtering.
    """

    queryset = CourseModel.objects.select_related("created_by").filter(is_active=True)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ["title", "description"]
    ordering_fields = [ "start_date", "end_date"]
    ordering = ["-start_date"]  # Default ordering
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return CourseListSerializer
        elif self.action == "enroll":
            return CourseEnrollSerializer
        return CourseDetailSerializer

    def get_permissions(self):
        """All actions use IsAuthenticated - specific permissions handled by decorators."""
        return super().get_permissions()

    def can_modify_course(self, course, user):
        """Check if user can modify (update/delete) this course."""
        # Course creator can always modify
        if course.created_by == user:
            return True
            
        # Teaching assistants can modify
        if course.teaching_assistants.filter(id=user.id).exists():
            return True
            
        # Students can NOT modify courses
        return False

    @course_list_schema
    def list(self, request, *args, **kwargs):
        """List courses with filtering and search."""
        return super().list(request, *args, **kwargs)


    @course_detail_schema
    def retrieve(self, request, *args, **kwargs):
        """Retrieve course details."""
        response = super().retrieve(request, *args, **kwargs)
        return ResponsePresenter.success_response(
            data=response.data,
            message="Course details retrieved successfully.",
        )
    @course_create_schema
    @laboratory_assistant_only  
    def create(self, request, *args, **kwargs):
        """Create a new course - restricted to teaching staff."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            course = serializer.save(created_by=request.user, updated_by=request.user)
            
            # Auto-assign creator as Teaching Assistant if not already assigned
            if not course.teaching_assistants.filter(id=request.user.id).exists():
                course.teaching_assistants.add(request.user)
            
            response_serializer = CourseDetailSerializer(course, context={'request': request})
            return ResponsePresenter.created_response(
                data=response_serializer.data,
                message="Course created successfully.",
            )
        return ResponsePresenter.bad_request_response(
            message="Validation failed",
            errors=serializer.errors
        )

    @course_update_schema
    @laboratory_assistant_only
    def partial_update(self, request, *args, **kwargs):
        """Update course information - restricted to course creators and TAs."""
        instance = self.get_object()
        
        # Check if user can modify this course
        if not self.can_modify_course(instance, request.user):
            return ResponsePresenter.forbidden_response(
                message="You do not have permission to update this course. Only course creators and teaching assistants can update courses.",
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            course = serializer.save(updated_by=request.user)
            response_serializer = CourseDetailSerializer(course, context={'request': request})
            return ResponsePresenter.success_response(
                data=response_serializer.data,
                message="Course updated successfully.",
            )
        return ResponsePresenter.bad_request_response(
            message="Validation failed",
            errors=serializer.errors
        )

    @course_destroy_schema
    @laboratory_assistant_only
    def destroy(self, request, *args, **kwargs):
        """Soft delete a course - restricted to course creators and TAs."""
        instance = self.get_object()
        
        # Check if user can modify this course
        if not self.can_modify_course(instance, request.user):
            return ResponsePresenter.forbidden_response(
                message="You do not have permission to delete this course. Only course creators and teaching assistants can delete courses.",
            )
        
        instance.is_active = False
        instance.updated_by = request.user
        instance.save()

        return ResponsePresenter.no_content_response(
            message="Course deleted successfully.",
        )

    @course_enroll_schema
    @action(detail=True, methods=["post"])
    def enroll(self, request, pk=None):
        """Enroll user in course using course ID."""
        try:
            course = self.get_object()

            # Validate enroll_key if provided in request data
            enroll_key = request.data.get("enroll_key")
            if enroll_key:
                if not course.enroll_key or enroll_key != course.enroll_key:
                    return ResponsePresenter.bad_request_response(
                        message="Invalid enrollment key.",
                    )

            # Pre-check if user can enroll to avoid unnecessary processing
            if not course.can_enroll_student(request.user):
                return ResponsePresenter.bad_request_response(
                    message="You are not eligible to enroll in this course or are already enrolled.",
                )

            # Attempt enrollment with atomic transaction
            enrollment_successful = course.enroll_student(request.user)
            
            if enrollment_successful:
                # Refresh course object to get updated data
                course.refresh_from_db()
                response_serializer = CourseDetailSerializer(course, context={'request': request})
                return ResponsePresenter.success_response(
                    data=response_serializer.data,
                    message="Successfully enrolled in the course.",
                )
            else:
                return ResponsePresenter.bad_request_response(
                    message="Failed to enroll in the course. Please try again.",
                )
                
        except Exception as e:
            return ResponsePresenter.internal_server_error_response(
                message="An error occurred during enrollment. Please try again later."
            )


    @course_my_courses_schema
    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get courses related to current user (student enrollments or TA assignments)."""
        user = request.user

        try:
            enrolled_courses = user.enrolled_courses.filter(is_active=True)
            assigned_courses = user.assigned_courses.filter(is_active=True)

            my_courses = (enrolled_courses | assigned_courses).distinct()

            filterset = self.filterset_class(request.GET, queryset=my_courses)
            if filterset.is_valid():
                my_courses = filterset.qs

            page = self.paginate_queryset(my_courses)
            if page is not None:
                serializer = CourseListSerializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)

            serializer = CourseListSerializer(my_courses, many=True, context={'request': request})
            return ResponsePresenter.success_response(
                data=serializer.data,
                message="My courses retrieved successfully.",
            )
        except Exception as e:
            return ResponsePresenter.internal_server_error_response(
                message=f"Error retrieving your courses: {str(e)}"
            )
