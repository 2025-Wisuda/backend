"""OpenAPI schema definitions for course session management endpoints."""

from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema

from shared.schemas import ResponseSchema

from ..serializers import CourseSessionDetailSerializer

course_session_detail_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        CourseSessionDetailSerializer, name="CourseSessionDetailResponse"
    ),
    summary="Retrieve course session details",
    description="Get detailed course session information with teaching assistant assignments.",
    tags=["Course Session"],
)

course_session_create_schema = extend_schema(
    request=CourseSessionDetailSerializer,
    responses=ResponseSchema.get_response_schema(
        CourseSessionDetailSerializer, name="CourseSessionCreateResponse"
    ),
    summary="Create course session",
    description="Create new course session with schedule validation.",
    tags=["Course Session"],
)

course_session_update_schema = extend_schema(
    request=CourseSessionDetailSerializer,
    responses=ResponseSchema.get_response_schema(
        CourseSessionDetailSerializer, name="CourseSessionUpdateResponse"
    ),
    summary="Update course session (partial)",
    description="Update course session information and schedule.",
    tags=["Course Session"],
)

course_session_destroy_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        CourseSessionDetailSerializer, name="CourseSessionDeleteResponse"
    ),
    summary="Delete course session",
    description="Soft delete course session (marks as inactive).",
    tags=["Course Session"],
    operation_id="course_session_destroy",
)
