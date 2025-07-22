"""
User API Schemas

OpenAPI schema definitions for user management endpoints.
Provides comprehensive documentation for user CRUD operations and profile management.
"""

from core.enums import UserGroup
from drf_spectacular.utils import OpenApiParameter, extend_schema
from shared.schemas import ResponseSchema

from ..serializers import (
    UserDetailSerializer,
    UserListSerializer,
    UserProfileSerializer,
)

user_list_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        UserListSerializer, name="UserListResponse"
    ),
    parameters=[
        OpenApiParameter(
            "group",
            type=str,
            description=f"Filter by user group. Available options: {', '.join([group.value for group in UserGroup])}",
            enum=[group.value for group in UserGroup],
            required=False,
        ),
        OpenApiParameter(
            "search",
            type=str,
            description="Search users by username, first_name, last_name.",
            required=False,
        ),
        OpenApiParameter(
            "page", type=int, description="Page number for pagination", required=False
        ),
        OpenApiParameter(
            "page_size",
            type=int,
            description="Number of users per page",
            required=False,
        ),
    ],
    summary="List users",
    description="Retrieve a paginated list of users with optional filtering by group and search capabilities.",
    tags=["User"],
)

# user_detail_schema = extend_schema(
#     responses=ResponseSchema.get_response_schema(
#         UserDetailSerializer, name="UserDetailResponse"
#     ),
#     summary="Retrieve user details",
#     description="Get detailed information about a specific user including their groups and permissions.",
#     tags=["User"],
# )

user_profile_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        UserProfileSerializer, name="UserProfileResponse"
    ),
    summary="Retrieve user profile",
    description="Get the profile information of the currently authenticated user.",
    tags=["User"],
)

update_user_profile_schema = extend_schema(
    request=UserProfileSerializer,
    responses=ResponseSchema.get_response_schema(
        UserProfileSerializer, name="UpdateUserProfileResponse"
    ),
    summary="Update user profile",
    description="Update the profile information of the currently authenticated user. Only provided fields will be updated.",
    tags=["User"],
)
