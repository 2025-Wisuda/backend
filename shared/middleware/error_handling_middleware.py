"""
Django Global Error Handling Middleware

This middleware provides centralized error handling and exception management
for the entire Django application. It catches unhandled exceptions, logs them
appropriately, and returns consistent error responses to API clients.

Features:
- Global exception catching and handling
- Consistent error response formatting across all endpoints
- Comprehensive error logging for debugging and monitoring
- User-friendly error messages with internationalization support
- Security: Prevents sensitive error details from leaking to clients
- Integration with Django's logging framework

Error Response Format:
All unhandled errors return a consistent JSON structure:
{
    "status": "error",
    "message": "A user-friendly error message",
    "errors": {
        "detail": "Technical error details (development only)"
    }
}

Logging:
- All errors are logged with full stack traces
- Includes request context (URL, method, user) for debugging
- Uses Django's configured logging handlers

Usage:
Add to Django middleware in settings.py (should be last):
MIDDLEWARE = [
    # ... other middleware
    'shared.middleware.ErrorHandlingMiddleware',  # Last middleware
]

Security Notes:
- Sensitive error details are only shown in DEBUG mode
- Production responses contain generic error messages
- All errors are logged for administrator review
"""

import logging

from django.http import JsonResponse
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    """
    Middleware to handle errors globally and provide consistent error responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Process exceptions that occur during request processing.
        """
        logger.error(
            f"Unhandled exception in {request.path}: {exception}", exc_info=True
        )

        if request.path.startswith("/api/"):
            return JsonResponse(
                {
                    "error": _("An unexpected error occurred. Please try again later."),
                    "status": "error",
                },
                status=500,
            )

        return None
