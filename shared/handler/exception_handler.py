"""
Django REST Framework Custom Exception Handler

This module provides a centralized exception handler for Django REST Framework
that ensures consistent error response formatting across all API endpoints.
It maps various exception types to standardized response formats with proper
HTTP status codes and user-friendly error messages.

Features:
- Standardized error response format for all API exceptions
- Proper HTTP status code mapping for different exception types
- User-friendly error messages with internationalization support
- Integration with custom response presenter for consistent formatting
- Fallback handling for unexpected exceptions

Supported Exception Types:
- 400 Bad Request: ValidationError, ParseError
- 401 Unauthorized: AuthenticationFailed, NotAuthenticated
- 403 Forbidden: PermissionDenied
- 404 Not Found: NotFound
- 409 Conflict: Custom business logic conflicts
- 429 Too Many Requests: Throttled
- 500 Internal Server Error: Unexpected exceptions
- 503 Service Unavailable: Service temporarily unavailable

Usage:
Configure in Django settings.py:
    REST_FRAMEWORK = {
        'EXCEPTION_HANDLER': 'shared.handler.custom_exception_handler',
    }
"""

from rest_framework.exceptions import APIException

from ..presenter.response_presenter import ResponsePresenter


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler that returns standardized error responses.

    Maps DRF APIException status codes to custom response formats for
    consistent API error handling. Falls back to a generic 500 error for
    unhandled exceptions.

    To use, set in REST_FRAMEWORK settings as the exception handler.
    """

    if isinstance(exc, APIException):
        status_code = exc.status_code
        message = str(exc.detail)
        errors = exc.get_full_details()

        if status_code == 400:
            return ResponsePresenter.bad_request_response(message, errors=errors)
        elif status_code == 401:
            return ResponsePresenter.unauthorized_response(message)
        elif status_code == 403:
            return ResponsePresenter.forbidden_response(message)
        elif status_code == 404:
            return ResponsePresenter.not_found_response(message)
        elif status_code == 409:
            return ResponsePresenter.conflict_response(message)
        elif status_code == 429:
            return ResponsePresenter.too_many_requests_response(message)
        elif status_code == 500:
            return ResponsePresenter.internal_server_error_response(message)
        elif status_code == 503:
            return ResponsePresenter.service_unavailable_response(message)

    error_message = f"Internal server error: {str(exc)}"
    return ResponsePresenter.internal_server_error_response(error_message)
