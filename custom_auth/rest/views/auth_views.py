"""
Authentication Views

ViewSet for authentication operations including password change and logout.
Implements JWT token management and secure authentication workflows.
"""

from django.contrib.auth import get_user_model
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from shared.presenter import ResponsePresenter

from ..schemas import change_password_schema, logout_schema
from ..serializers import ChangePasswordSerializer, LogoutRequestSerializer

User = get_user_model()


class AuthViewSet(GenericViewSet):
    """
    ViewSet for authentication operations.

    Endpoints:
    - change_password: Update user password with validation
    - logout: Invalidate JWT refresh token
    """

    def get_serializer_class(self):
        if self.action == "change_password":
            return ChangePasswordSerializer
        elif self.action == "logout":
            return LogoutRequestSerializer
        return super().get_serializer_class()

    @change_password_schema
    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
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
    @permission_classes([AllowAny])
    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return ResponsePresenter.bad_request_response(
                message="Invalid input data",
                errors=serializer.errors,
            )

        try:
            # Handle refresh token blacklist
            refresh_token = serializer.validated_data.get("refresh_token")
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except Exception as token_error:
                    # If token is invalid/expired, we still consider logout successful
                    pass

            # Auto unregister FCM device for authenticated user
            if request.user.is_authenticated:
                try:
                    from fcm_notifications.models import FCMDeviceModel

                    # Deactivate all devices for this user
                    devices = FCMDeviceModel.objects.filter(
                        user=request.user, is_active=True
                    )
                    if devices.exists():
                        devices.update(is_active=False)
                except Exception as fcm_error:
                    # Log error but don't fail logout
                    pass

            return ResponsePresenter.success_response(
                message="Successfully logged out",
                data={"detail": "Successfully logged out"},
            )
        except Exception as e:
            # Even if there's an error, we consider logout successful
            return ResponsePresenter.success_response(
                message="Successfully logged out",
                data={"detail": "Successfully logged out"},
            )
