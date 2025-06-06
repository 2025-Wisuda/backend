"""
Shared presenter package for API response standardization.

This package provides utilities for creating consistent API responses across
the Django REST Framework application. The presenter classes ensure uniform
response structures, proper HTTP status codes, and standardized error handling.

Main Components:
- ResponsePresenter: Class for creating standardized API responses with proper
  status codes, messages, and data formatting

Features:
- Consistent response structure across all API endpoints
- Built-in internationalization support using Django's translation system
- Proper HTTP status code handling for various scenarios
- Error response formatting with detailed error information
- Success response formatting with optional data payload

Response Structure:
All responses follow a consistent structure:
{
    "status": "success" | "error",
    "message": "Human-readable message",
    "data": <response_payload>,  // Optional, only in success responses
    "errors": <error_details>    // Optional, only in error responses
}

Usage Examples:
    from shared.presenter import ResponsePresenter
    
    # Success responses
    return ResponsePresenter.success_response(
        "User retrieved successfully", 
        data=user_data
    )
    
    # Error responses
    return ResponsePresenter.not_found_response(
        "User with ID {user_id} not found",
        user_id=123
    )
    
    # Creation responses
    return ResponsePresenter.created_response(
        "User created successfully",
        data=new_user_data
    )

Available Response Methods:
- success_response(): HTTP 200 - General success
- created_response(): HTTP 201 - Resource created
- no_content_response(): HTTP 204 - Success with no content
- bad_request_response(): HTTP 400 - Invalid request
- unauthorized_response(): HTTP 401 - Authentication required
- forbidden_response(): HTTP 403 - Access denied
- not_found_response(): HTTP 404 - Resource not found
- conflict_response(): HTTP 409 - Resource conflict
- too_many_requests_response(): HTTP 429 - Rate limit exceeded
- internal_server_error_response(): HTTP 500 - Server error
- service_unavailable_response(): HTTP 503 - Service unavailable
"""

from .response_presenter import ResponsePresenter

__all__ = [
    "ResponsePresenter",
]
