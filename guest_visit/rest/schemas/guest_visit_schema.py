"""
API schemas for Guest Visit endpoints.

Provides OpenAPI documentation for guest visit CRUD operations
with proper request/response schemas.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import serializers

from shared.schemas import ResponseSchema

from ..serializers import GuestVisitDetailSerializer, GuestVisitListSerializer


class GuestVisitDeleteResponseSerializer(serializers.Serializer):
    """Serializer for guest visit delete response."""
    
    data = serializers.CharField()

# Guest visit list schema
guest_visit_list_schema = extend_schema(
    responses=ResponseSchema.get_list_response_schema(
        GuestVisitListSerializer, name="GuestVisitListResponse"
    ),
    summary="List guest visits",
    description="Retrieve a paginated list of guest visits with filtering and search capabilities.",
    tags=["Guest Visit"],
)

# Guest visit detail schema
guest_visit_detail_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        GuestVisitDetailSerializer, name="GuestVisitDetailResponse"
    ),
    summary="Retrieve guest visit details",
    description="Get detailed information about a specific guest visit.",
    tags=["Guest Visit"],
)

# Guest visit create schema
guest_visit_create_schema = extend_schema(
    request=GuestVisitDetailSerializer,
    responses=ResponseSchema.get_response_schema(
        GuestVisitDetailSerializer, name="GuestVisitCreateResponse"
    ),
    summary="Create guest visit",
    description="Create a new guest visit entry. Can be either manual entry or registered user selection.",
    tags=["Guest Visit"],
)

# Guest visit update schema
guest_visit_update_schema = extend_schema(
    request=GuestVisitDetailSerializer,
    responses=ResponseSchema.get_response_schema(
        GuestVisitDetailSerializer, name="GuestVisitUpdateResponse"
    ),
    summary="Update guest visit",
    description="Update an existing guest visit. Only allowed within 5 minutes of creation.",
    tags=["Guest Visit"],
)

# Guest visit delete schema
guest_visit_delete_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        GuestVisitDeleteResponseSerializer, name="GuestVisitDeleteResponse"
    ),
    summary="Delete guest visit",
    description="Soft delete a guest visit (set is_active to False). Only allowed within 5 minutes of creation.",
    tags=["Guest Visit"],
)
