"""
ViewSet classes for course session API endpoints.

This module provides ViewSet classes for course session models
with nested routing support for better API structure.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from shared.presenter import ResponsePresenter
from shared.utils.permission_config_utils import laboratory_assistant_only

from ...models import CourseSessionModel
from ..schemas import (
    course_session_create_schema,
    course_session_destroy_schema,
    course_session_detail_schema,
    course_session_update_schema,
)
from ..serializers import CourseSessionDetailSerializer, CourseSessionListSerializer


@extend_schema_view(
    list=extend_schema(exclude=True),
)
class CourseSessionViewSet(ModelViewSet):
    """
    ViewSet for course session management.

    Provides CRUD operations for course sessions with schedule validation
    and lab integration. Supports both nested and flat routing.
    """

    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        """Get queryset with course filtering for nested routes."""
        queryset = CourseSessionModel.objects.select_related(
            "course", "created_by"
        ).filter(is_active=True)

        course_pk = self.kwargs.get("course_pk")
        if course_pk:
            queryset = queryset.filter(course_id=course_pk)

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return CourseSessionListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return CourseSessionDetailSerializer
        return CourseSessionDetailSerializer

    def get_permissions(self):
        """All actions use IsAuthenticated - specific permissions handled by decorators."""
        return super().get_permissions()

    def perform_create(self, serializer):
        """Handle creation with nested course assignment."""
        course_pk = self.kwargs.get("course_pk")
        if course_pk:
            from ...models import CourseModel

            course = CourseModel.objects.get(pk=course_pk, is_active=True)
            serializer.save(
                course=course,
                created_by=self.request.user,
                updated_by=self.request.user,
            )
        else:
            # For flat routes, use provided course
            serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def get_serializer_context(self):
        """Add course to context for nested routes."""
        context = super().get_serializer_context()
        course_pk = self.kwargs.get("course_pk")
        if course_pk:
            from ...models import CourseModel

            try:
                course = CourseModel.objects.get(pk=course_pk, is_active=True)
                context["course"] = course
            except CourseModel.DoesNotExist:
                pass
        return context

    @course_session_detail_schema
    def retrieve(self, request, *args, **kwargs):
        """Retrieve course session details."""
        response = super().retrieve(request, *args, **kwargs)
        return ResponsePresenter.success_response(
            data=response.data,
            message="Course session retrieved successfully.",
        )

    @course_session_create_schema
    @laboratory_assistant_only
    def create(self, request, *args, **kwargs):
        """Create a new course session - restricted to teaching staff."""
        # Debug logging (without accessing request.body)
        import logging
        logger = logging.getLogger("application.course")
        logger.info("Course session creation - User: %s, Course PK: %s", 
                   request.user, self.kwargs.get('course_pk'))
        logger.info("Request data: %s", request.data)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = CourseSessionDetailSerializer(serializer.instance)
        return ResponsePresenter.created_response(
            data=response_serializer.data,
            message="Course session created successfully.",
        )

    @course_session_update_schema
    @laboratory_assistant_only
    def partial_update(self, request, *args, **kwargs):
        """Update course session information - restricted to teaching staff."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        session = serializer.save(updated_by=request.user)

        response_serializer = CourseSessionDetailSerializer(session)
        return ResponsePresenter.success_response(
            data=response_serializer.data,
            message="Course session updated successfully.",
        )

    @course_session_destroy_schema
    @laboratory_assistant_only
    def destroy(self, request, *args, **kwargs):
        """Soft delete a course session - restricted to teaching staff."""
        instance = self.get_object()
        instance.is_active = False
        instance.updated_by = request.user
        instance.save()

        return ResponsePresenter.no_content_response(
            message="Course session deleted successfully.",
        )
