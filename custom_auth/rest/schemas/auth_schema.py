"""
Authentication API schema definitions.

This module provides OpenAPI schema configurations for authentication endpoints
using drf-spectacular decorators for automatic API documentation generation.
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
    description="Change the password for the authenticated user",
    summary="Change Password",
    operation_id="change_password",
)

logout_schema = extend_schema(
    request=LogoutRequestSerializer,
    responses=ResponseSchema.get_response_schema(
        AuthLogoutResponseSerializer, name="LogoutResponse"
    ),
    description="Logout the authenticated user and invalidate their session",
    summary="Logout User",
    operation_id="logout_user",
)
