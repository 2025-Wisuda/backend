from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiTypes, extend_schema_field


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "data": data,
                "meta": {
                    "pagination": {
                        "next": self.get_next_link(),
                        "previous": self.get_previous_link(),
                        "total_items": self.page.paginator.count,
                        "total_pages": self.page.paginator.num_pages,
                        "current_page": self.page.number,
                        "page_size": self.page_size,
                    },
                },
            }
        )

    @extend_schema_field(
        {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {"type": "object"},
                },
                "meta": {
                    "type": "object",
                    "properties": {
                        "pagination": {
                            "type": "object",
                            "properties": {
                                "next": {"type": "string", "nullable": True},
                                "previous": {"type": "string", "nullable": True},
                                "total_items": {"type": "integer"},
                                "total_pages": {"type": "integer"},
                                "current_page": {"type": "integer"},
                                "page_size": {"type": "integer"},
                            },
                        },
                    },
                },
            },
        }
    )
    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "data": schema,
                "meta": {
                    "type": "object",
                    "properties": {
                        "pagination": {
                            "type": "object",
                            "properties": {
                                "next": {"type": "string", "nullable": True},
                                "previous": {"type": "string", "nullable": True},
                                "total_items": {"type": "integer"},
                                "total_pages": {"type": "integer"},
                                "current_page": {"type": "integer"},
                                "page_size": {"type": "integer"},
                            },
                        },
                    },
                },
            },
        }
