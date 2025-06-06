"""
Response presenter utilities for API responses.

This module provides standardized response formatting functions for REST API
endpoints, ensuring consistent response structure across the application.
"""

from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.response import Response


class ResponsePresenter:
    """
    A class for creating standardized API responses.

    This class provides methods for creating consistent response structures
    across the application with proper status codes and error handling.
    """

    @staticmethod
    def build_response(
        status_value: str,
        message: str,
        data=None,
        errors=None,
        status_code=status.HTTP_200_OK,
    ):
        """
        Build standardized API response structure.

        Args:
            status_value: Response status indicator (success/error)
            message: Human-readable response message
            data: Optional response data payload
            errors: Optional error details
            status_code: HTTP status code

        Returns:
            Response: DRF Response object with standardized structure
        """
        response = {
            "status": status_value,
            "message": message,
            "data": data,
        }
        if errors:
            response["errors"] = errors
        return Response(response, status=status_code)

    @classmethod
    def success_response(cls, message: str, data=None, **kwargs):
        """
        Create successful response with data.

        Args:
            message: Success message to display
            data: Optional data payload

        Returns:
            Response: Success response with 200 status
        """
        return cls.build_response(
            status_value="success",
            message=_(message).format(**kwargs),
            data=data,
            status_code=status.HTTP_200_OK,
        )

    @classmethod
    def created_response(cls, message: str, data=None, **kwargs):
        """
        Create successful creation response.

        Args:
            message: Creation success message
            data: Optional created resource data
            **kwargs: Format parameters for message

        Returns:
            Response: Success response with 201 status
        """
        return cls.build_response(
            status_value="success",
            message=_(message).format(**kwargs),
            data=data,
            status_code=status.HTTP_201_CREATED,
        )

    @classmethod
    def no_content_response(cls, message: str):
        """
        Create response indicating no content.

        Args:
            message: Message to display

        Returns:
            Response: Success response with 204 status
        """
        return cls.build_response(
            status_value="success",
            message=_(message),
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @classmethod
    def bad_request_response(cls, message: str, errors=None, **kwargs):
        """
        Create response for bad request.

        Args:
            message: Error message
            errors: Optional list of error details
            **kwargs: Format parameters for message

        Returns:
            Response: Error response with 400 status
        """
        return cls.build_response(
            status_value="error",
            message=_(message).format(**kwargs),
            errors=errors,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    @classmethod
    def unauthorized_response(cls, message: str, **kwargs):
        """
        Create response for unauthorized access.

        Args:
            message: Error message
            **kwargs: Format parameters for message

        Returns:
            Response: Error response with 401 status
        """
        try:
            formatted_message = _(message).format(**kwargs)
        except KeyError:
            formatted_message = _(message)

        return cls.build_response(
            status_value="error",
            message=formatted_message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    @classmethod
    def forbidden_response(cls, message: str, **kwargs):
        """
        Create response for forbidden access.

        Args:
            message: Error message
            **kwargs: Format parameters for message

        Returns:
            Response: Error response with 403 status
        """
        return cls.build_response(
            status_value="error",
            message=_(message).format(**kwargs),
            status_code=status.HTTP_403_FORBIDDEN,
        )

    @classmethod
    def not_found_response(cls, message: str, **kwargs):
        """
        Create response when a resource is not found.

        Args:
            message: Error message
            **kwargs: Format parameters for message

        Returns:
            Response: Error response with 404 status
        """
        return cls.build_response(
            status_value="error",
            message=_(message).format(**kwargs),
            status_code=status.HTTP_404_NOT_FOUND,
        )

    @classmethod
    def conflict_response(cls, message: str, **kwargs):
        """
        Create response for conflict.

        Args:
            message: Error message
            **kwargs: Format parameters for message

        Returns:
            Response: Error response with 409 status
        """
        return cls.build_response(
            status_value="error",
            message=_(message).format(**kwargs),
            status_code=status.HTTP_409_CONFLICT,
        )

    @classmethod
    def too_many_requests_response(cls, message: str, **kwargs):
        """
        Create response indicating too many requests.

        Args:
            message: Error message
            **kwargs: Format parameters for message

        Returns:
            Response: Error response with 429 status
        """
        return cls.build_response(
            status_value="error",
            message=_(message).format(**kwargs),
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    @classmethod
    def internal_server_error_response(cls, message: str, **kwargs):
        """
        Create response for internal server error.

        Args:
            message: Error message
            **kwargs: Format parameters for message

        Returns:
            Response: Error response with 500 status
        """
        return cls.build_response(
            status_value="error",
            message=_(message).format(**kwargs),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @classmethod
    def service_unavailable_response(cls, message: str, **kwargs):
        """
        Create response when the service is unavailable.

        Args:
            message: Error message
            **kwargs: Format parameters for message

        Returns:
            Response: Error response with 503 status
        """
        return cls.build_response(
            status_value="error",
            message=_(message).format(**kwargs),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
