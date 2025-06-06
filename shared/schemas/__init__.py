"""
Shared schemas package for API response standardization.

This package provides utilities for creating consistent API response structures
and OpenAPI documentation schemas. It includes base serializer classes and
response schema generators for Django REST Framework applications.

Main Components:
- ResponseSchema: Class for generating OpenAPI response schemas
- Serializer classes: Base serializers for standardized API responses
- Response utilities: Helper functions for creating consistent response formats

Usage:
    from shared.schemas import ResponseSchema, GetListResponseSerializer
    
    # Generate OpenAPI schema
    schema = ResponseSchema.get_list_response_schema(UserSerializer, "UserListResponse")
    
    # Use base serializers for documentation
    class UserListView(ListAPIView):
        serializer_class = GetListResponseSerializer
"""

from .response_schema import ResponseSchema
from .serializer_schema import (
    GetListResponseSerializer,
    GetResponseSerializer,
    MetaSerializer,
    PaginationMetaSerializer,
)

__all__ = [
    "MetaSerializer",
    "PaginationMetaSerializer",
    "GetListResponseSerializer",
    "GetResponseSerializer",
    "ResponseSchema",
]
