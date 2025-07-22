"""OpenAPI schema definitions for course management endpoints."""

from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema

from shared.schemas import ResponseSchema

from ..serializers import (
    CourseDetailSerializer,
    CourseEnrollSerializer,
    CourseListSerializer,
)

course_list_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        CourseListSerializer, name="CourseListResponse"
    ),
    parameters=[
        OpenApiParameter(
            "search",
            type=str,
            description="Search in course title and description",
            required=False,
        )
    ],
    summary="List courses",
    description="Retrieve a paginated list of courses with search and ordering capabilities.",
    tags=["Course"],
)

course_detail_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        CourseDetailSerializer, name="CourseDetailResponse"
    ),
    summary="Retrieve course details",
    description="Get detailed information about a specific course including enrolled students and teaching assistants.",
    tags=["Course"],
)

course_create_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        CourseDetailSerializer, name="CourseCreateResponse"
    ),
    summary="Create course",
    description="Create a new course with basic information.",
    tags=["Course"],
)

course_update_schema = extend_schema(
    request=CourseDetailSerializer,
    responses=ResponseSchema.get_response_schema(
        CourseDetailSerializer, name="CourseUpdateResponse"
    ),
    summary="Update course (partial)",
    description="Update course information and enrollment settings. Only provided fields will be updated.",
    tags=["Course"],
)

course_enroll_schema = extend_schema(
    request=CourseEnrollSerializer,
    responses=ResponseSchema.get_response_schema(
        CourseDetailSerializer, name="CourseEnrollResponse"
    ),
    summary="Enroll in course",
    description="Enroll student in course using enrollment key.",
    tags=["Course"],
)

course_my_courses_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        CourseListSerializer, name="MyCourseListResponse"
    ),
    parameters=[
        OpenApiParameter(
            "search",
            type=str,
            description="Search in course title and description",
            required=False,
        ),
        OpenApiParameter(
            "start_date",
            type=str,
            description="Filter courses starting from this date (YYYY-MM-DD)",
            required=False,
        ),
        OpenApiParameter(
            "end_date", 
            type=str,
            description="Filter courses ending until this date (YYYY-MM-DD)",
            required=False,
        ),
        OpenApiParameter(
            "page",
            type=int,
            description="Page number for pagination",
            required=False,
        ),
        OpenApiParameter(
            "page_size",
            type=int,
            description="Number of items per page",
            required=False,
        ),
    ],
    summary="Get my courses",
    description="Retrieve paginated list of courses where current user is either enrolled as student or assigned as teaching assistant. Supports search and date filtering.",
    tags=["Course"],
)

course_destroy_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        CourseDetailSerializer, name="CourseDeleteResponse"
    ),
    summary="Delete course",
    description="Soft delete a course (marks as inactive).",
    tags=["Course"],
    operation_id="course_destroy",
)
