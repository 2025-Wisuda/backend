"""
Custom pagination for standardized API responses.

- Uses DRF's PageNumberPagination
- Returns data with status, message, and pagination metadata
- Compatible with OpenAPI and frontend pagination
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    """
    Page-based pagination with consistent response format.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    message = "Data retrieved successfully"
    status = "success"

    def get_paginated_response(self, data, message=None, status=None):
        """
        Return standardized paginated response.

        Args:
            data (list): Serialized items
            message (str): Optional custom message
            status (str): Optional custom status

        Returns:
            Response: {
                "status": "success",
                "message": "Data retrieved successfully",
                "data": [...],
                "meta": {
                    "pagination": {
                        "next": URL | null,
                        "previous": URL | null,
                        "total_items": int,
                        "total_pages": int,
                        "current_page": int,
                        "page_size": int
                    }
                }
            }
        """
        return Response(
            {
                "status": status or self.status,
                "message": message or self.message,
                "data": data,
                "meta": {
                    "pagination": {
                        "next": self.get_next_link(),
                        "previous": self.get_previous_link(),
                        "total_items": self.page.paginator.count,
                        "total_pages": self.page.paginator.num_pages,
                        "current_page": self.page.number,
                        "page_size": self.get_page_size(self.request),
                    }
                },
            }
        )
