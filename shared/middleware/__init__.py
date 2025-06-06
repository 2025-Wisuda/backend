"""
Shared middleware package for Django application request/response processing.

This package provides custom middleware components that handle cross-cutting
concerns across the entire Django application. These middleware classes
process requests and responses globally, providing consistent behavior
for error handling, internationalization, and permission checking.

Main Components:
- ErrorHandlingMiddleware: Global exception handling and error response formatting
- LanguageParameterMiddleware: Dynamic language switching based on query parameters
- PermissionMiddleware: Automatic permission checking for API endpoints

Key Features:
- Global error handling with consistent API response format
- Dynamic language switching via URL parameters
- Automatic permission enforcement based on 4-level system
- Route-based permission checking for API endpoints
- Logging and monitoring of application errors
- Internationalization support for multi-language applications
- Graceful error recovery and user-friendly error messages

Middleware Order:
When adding these middleware to Django settings, consider the following order:
1. LanguageParameterMiddleware - Should be early to set language context
2. ErrorHandlingMiddleware - Should be late to catch all exceptions

Usage in Django Settings:
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'shared.middleware.LanguageParameterMiddleware',  # Early in the stack
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'shared.middleware.ErrorHandlingMiddleware',  # Late in the stack
    ]


ErrorHandlingMiddleware:
- Catches unhandled exceptions throughout the application
- Provides consistent JSON error responses for API endpoints
- Logs detailed error information for debugging and monitoring
- Returns user-friendly error messages with proper HTTP status codes
- Only processes API endpoints (paths starting with '/api/')

LanguageParameterMiddleware:
- Allows dynamic language switching via 'lang' query parameter
- Validates language codes against Django's LANGUAGES setting
- Falls back to default language for invalid language codes
- Persists language preference in user session
- Activates Django's translation system for the selected language

Example Usage:
    # Permission checking via middleware (automatic)
    GET /api/courses/       # Requires PUBLIC_ACCESS (all users)
    POST /api/courses/      # Requires STAFF_ACCESS (Teaching Assistants+)
    DELETE /api/courses/1/  # Requires STAFF_ACCESS (Teaching Assistants+)
    
    # Language switching via URL parameter
    GET /api/users?lang=en  # Switch to English
    GET /api/users?lang=id  # Switch to Indonesian
    
    # Error handling for API endpoints
    # Any unhandled exception in /api/* routes will return:
    {
        "error": "An unexpected error occurred. Please try again later.",
        "status": "error"
    }
    
    # Permission denied responses:
    {
        "error": "Insufficient permissions. Required: create_course",
        "status": "error"
    }

Permission Decorators Usage:
    from shared.middleware.permission_middleware import require_permission
    from shared.constants.permission_constant import Permission
    
    @require_permission(Permission.COURSE.CREATE_COURSE)
    def create_course_view(request):
        # Only Teaching Assistants and above can access
        pass

Benefits:
- Automatic permission enforcement for all API routes
- Consistent error handling across all API endpoints
- User-friendly multilingual support
- Centralized logging and monitoring
- Graceful degradation for unsupported languages
- Improved security with route-based permission checking
- Simplified development with global error catching and permission management
"""

from .error_handling_middleware import ErrorHandlingMiddleware
from .language_middleware import LanguageParameterMiddleware

__all__ = [
    "ErrorHandlingMiddleware",
    "LanguageParameterMiddleware",
]
