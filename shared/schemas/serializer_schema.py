"""
Serializer schema utilities for OpenAPI documentation.

This module provides base serializer classes that define the standard response
structure for API endpoints. These serializers are used to generate consistent
OpenAPI documentation and ensure uniform response formats across the application.

The serializers defined here follow a standard response pattern:
- status: Indicates success or error
- message: Human-readable message
- data: The actual response payload
- meta: Additional metadata (for paginated responses)
"""

from rest_framework import serializers


class PaginationMetaSerializer(serializers.Serializer):
    """
    Serializer for pagination metadata in API responses.

    This serializer defines the structure for pagination information
    that is included in list endpoints to help clients navigate
    through paginated data.

    Fields:
        next (URLField): URL to the next page of results (null if last page)
        previous (URLField): URL to the previous page of results (null if first page)
        total_items (IntegerField): Total number of items across all pages
        total_pages (IntegerField): Total number of pages available
        current_page (IntegerField): Current page number (1-indexed)
        page_size (IntegerField): Number of items per page
    """

    next = serializers.URLField(
        allow_null=True, help_text="URL to the next page of results"
    )
    previous = serializers.URLField(
        allow_null=True, help_text="URL to the previous page of results"
    )
    total_items = serializers.IntegerField(
        help_text="Total number of items across all pages"
    )
    total_pages = serializers.IntegerField(help_text="Total number of pages available")
    current_page = serializers.IntegerField(help_text="Current page number (1-indexed)")
    page_size = serializers.IntegerField(help_text="Number of items per page")


class MetaSerializer(serializers.Serializer):
    """
    Serializer for metadata in API responses.

    This serializer wraps pagination and other metadata that may be
    included in API responses to provide additional context about
    the returned data.

    Fields:
        pagination (PaginationMetaSerializer): Pagination information for list responses
    """

    pagination = PaginationMetaSerializer(
        help_text="Pagination information for list responses"
    )


class GetListResponseSerializer(serializers.Serializer):
    """
    Base serializer for paginated list API responses.

    This serializer defines the standard structure for API responses
    that return a list of items with pagination metadata. It ensures
    consistent response format across all list endpoints.

    Fields:
        status (CharField): Response status indicator ("success" or "error")
        message (CharField): Human-readable response message
        data (ListField): Array of response data items
        meta (MetaSerializer): Metadata including pagination information

    Example response:
        {
            "status": "success",
            "message": "Users retrieved successfully",
            "data": [
                {"id": 1, "name": "John Doe"},
                {"id": 2, "name": "Jane Smith"}
            ],
            "meta": {
                "pagination": {
                    "next": "http://api.example.com/users?page=2",
                    "previous": null,
                    "total_items": 50,
                    "total_pages": 5,
                    "current_page": 1,
                    "page_size": 10
                }
            }
        }
    """

    status = serializers.CharField(
        help_text='Response status indicator ("success" or "error")'
    )
    message = serializers.CharField(help_text="Human-readable response message")
    data = serializers.ListField(
        child=serializers.DictField(), help_text="Array of response data items"
    )
    meta = MetaSerializer(help_text="Metadata including pagination information")


class GetResponseSerializer(serializers.Serializer):
    """
    Base serializer for single item API responses.

    This serializer defines the standard structure for API responses
    that return a single item without pagination. It ensures consistent
    response format across all detail endpoints.

    Fields:
        status (CharField): Response status indicator ("success" or "error")
        message (CharField): Human-readable response message
        data (DictField): Single response data object

    Example response:
        {
            "status": "success",
            "message": "User retrieved successfully",
            "data": {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com"
            }
        }
    """

    status = serializers.CharField(
        help_text='Response status indicator ("success" or "error")'
    )
    message = serializers.CharField(help_text="Human-readable response message")
    data = serializers.DictField(help_text="Single response data object")
