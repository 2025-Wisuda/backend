"""
Response schema utilities for OpenAPI documentation.

This module provides helper functions to dynamically generate response schemas
for drf-spectacular OpenAPI documentation with consistent structure.
"""

from drf_spectacular.utils import OpenApiResponse

from .serializer_schema import GetListResponseSerializer, GetResponseSerializer


class ResponseSchema:
    """
    A class for creating standardized OpenAPI response schemas.

    This class provides methods for creating consistent response schema structures
    for drf-spectacular OpenAPI documentation with proper type definitions.
    """

    @staticmethod
    def get_list_response_schema(data_serializer, name="DynamicGetListResponse"):
        """
        Generate OpenAPI response schema for paginated list endpoints.

        Args:
            data_serializer: Serializer class for the data items
            name: Reference name for the generated schema

        Returns:
            OpenApiResponse: Response schema for list endpoints
        """

        class Meta:
            ref_name = name

        DynamicGetListResponseSerializer = type(
            name,
            (GetListResponseSerializer,),
            {
                "data": data_serializer(many=True),
                "Meta": Meta,
            },
        )
        return OpenApiResponse(response=DynamicGetListResponseSerializer)

    @staticmethod
    def get_response_schema(data_serializer, name="DynamicGetResponse"):
        """
        Generate OpenAPI response schema for single item endpoints.

        Args:
            data_serializer: Serializer class for the data item
            name: Reference name for the generated schema

        Returns:
            OpenApiResponse: Response schema for detail endpoints
        """

        class Meta:
            ref_name = name

        DynamicGetResponseSerializer = type(
            name,
            (GetResponseSerializer,),
            {
                "data": data_serializer(),
                "Meta": Meta,
            },
        )
        return OpenApiResponse(response=DynamicGetResponseSerializer)
