"""
Shared Handler Module - Exception Handling

This module provides centralized exception handling utilities for the Django
application. It ensures consistent error response formatting and proper
HTTP status code mapping across all API endpoints.

Main Components:
- custom_exception_handler: Django REST Framework exception handler that
  provides standardized error responses with consistent format

Key Features:
- Consistent error response structure across all endpoints
- Proper HTTP status code mapping for different exception types
- Detailed error information for development and debugging
- User-friendly error messages for production
- Integration with Django's logging system
- Support for internationalization in error messages

Error Response Format:
All errors follow a consistent structure:
{
    "status": "error",
    "message": "Human-readable error message",
    "errors": {
        "field_name": ["Field-specific error messages"],
        "non_field_errors": ["General error messages"]
    }
}

Usage in Django Settings:
    REST_FRAMEWORK = {
        'EXCEPTION_HANDLER': 'shared.handler.custom_exception_handler',
    }
"""

from .exception_handler import custom_exception_handler

__all__ = [
    "custom_exception_handler",
]
