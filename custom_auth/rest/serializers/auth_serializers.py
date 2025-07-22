"""
Authentication Serializers

Serializers for authentication-related operations including password change and logout.
Implements comprehensive validation for password security requirements.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change operations.

    Validates:
    - Current password correctness
    - New password strength (Django validators)
    - New password differs from current
    """

    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, attrs):
        old_password = attrs.get("old_password")
        new_password = attrs.get("new_password")

        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError("User not found in request context.")

        user = request.user

        if not user.check_password(old_password):
            raise serializers.ValidationError(
                {"old_password": "Current password is incorrect."}
            )

        if old_password == new_password:
            raise serializers.ValidationError(
                {
                    "new_password": "New password must be different from current password."
                }
            )

        return attrs


class AuthChangePasswordResponseSerializer(serializers.Serializer):
    """Serializer for password change response data."""

    data = serializers.CharField()


class LogoutRequestSerializer(serializers.Serializer):
    """Serializer for logout request containing refresh token."""

    refresh_token = serializers.CharField(help_text="Refresh token to be blacklisted")


class AuthLogoutResponseSerializer(serializers.Serializer):
    """Serializer for logout response data."""

    data = serializers.CharField()
