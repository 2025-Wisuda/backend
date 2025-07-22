"""
Authentication API Schemas

OpenAPI schema definitions for authentication endpoints.
Provides comprehensive documentation for password change and logout operations.
"""

from drf_spectacular.utils import extend_schema

from shared.schemas import ResponseSchema

from ..serializers import (
    AuthChangePasswordResponseSerializer,
    AuthLogoutResponseSerializer,
    ChangePasswordSerializer,
    LogoutRequestSerializer,
)

change_password_schema = extend_schema(
    request=ChangePasswordSerializer,
    responses=ResponseSchema.get_response_schema(
        AuthChangePasswordResponseSerializer, name="ChangePasswordResponse"
    ),
    summary="Change password",
    description="Change user password with validation.",
    operation_id="change_password",
)

logout_schema = extend_schema(
    request=LogoutRequestSerializer,
    responses=ResponseSchema.get_response_schema(
        AuthLogoutResponseSerializer, name="LogoutResponse"
    ),
    summary="Logout user",
    description="Logout user and invalidate session.",
    operation_id="logout_user",
)
