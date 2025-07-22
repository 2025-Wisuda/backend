"""
Custom Auth REST API

RESTful API implementation for user management and authentication.

This package provides:
- User CRUD operations with filtering and search
- Profile management (self-service)
- Authentication endpoints (login, logout, password change)
- JWT token management
- OpenAPI documentation with drf-spectacular

API Structure:
- filters/: Django-filters for queryset filtering
- schemas/: OpenAPI schema definitions for documentation
- serializers/: DRF serializers for data validation and transformation
- views/: ViewSets for API endpoints
- urls/: URL routing configuration

Authentication Flow:
1. Login with username/password → JWT tokens
2. Use access token for API requests
3. Refresh tokens when expired
4. Logout to blacklist refresh token
"""
