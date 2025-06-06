"""
Authentication ViewSet for handling auth-related API endpoints.

Provides endpoints for:
- Change password (POST /auth/change-password)
- Logout (POST /auth/logout) - For shared lab computers security

Login and refresh token handled by SimpleJWT built-in views.
"""

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from shared.presenter import ResponsePresenter

from ..schemas import change_password_schema, logout_schema
from ..serializers import ChangePasswordSerializer, LogoutRequestSerializer

User = get_user_model()


class AuthViewSet(GenericViewSet):
    """
    ViewSet for authentication management.

    Provides authentication-related endpoints including
    password management for authenticated users.
    """

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "change_password":
            return ChangePasswordSerializer
        elif self.action == "logout":
            return LogoutRequestSerializer
        return super().get_serializer_class()

    @change_password_schema
    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        """Change current user's password."""
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            return ResponsePresenter.bad_request_response(
                message="Invalid input data",
                errors=serializer.errors,
            )

        new_password = serializer.validated_data["new_password"]
        request.user.set_password(new_password)
        if hasattr(request.user, "updated_by"):
            request.user.updated_by = request.user
        request.user.save()

        return ResponsePresenter.success_response(
            message="Password changed successfully",
            data={"detail": "Password has been updated successfully"},
        )

    @logout_schema
    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request):
        """Logout user by blacklisting refresh token."""
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return ResponsePresenter.bad_request_response(
                message="Invalid input data",
                errors=serializer.errors,
            )

        try:
            refresh_token = serializer.validated_data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return ResponsePresenter.success_response(
                message="Successfully logged out",
                data={"detail": "Successfully logged out"},
            )
        except Exception as e:
            return ResponsePresenter.bad_request_response(
                message="Failed to logout",
                errors={"detail": str(e)},
            )
