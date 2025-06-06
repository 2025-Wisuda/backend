"""
Authentication API serializers with Django built-in validation.

Provides serializers for authentication operations with proper validation
using Django's built-in password validators for consistency and reliability.

Key Features:
- Django built-in password validation for security requirements
- Write-only fields for sensitive data protection
- Standard Django password policy enforcement
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change operations.

    Features:
    - Write-only fields for password security
    - Django built-in password validation for security requirements
    - Required field validation for both old and new passwords
    """

    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        """
        Validate new password using Django's built-in validators.

        Ensures password meets Django's security requirements including:
        - Minimum length requirements
        - Character complexity requirements
        - Common password checks
        - User attribute similarity checks
        """
        try:
            validate_password(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value


class AuthChangePasswordResponseSerializer(serializers.Serializer):
    """Serializer for change password response."""

    data = serializers.CharField()


class LogoutRequestSerializer(serializers.Serializer):
    """Serializer for logout request."""

    refresh_token = serializers.CharField(help_text="Refresh token to be blacklisted")


class AuthLogoutResponseSerializer(serializers.Serializer):
    """Serializer for logout response."""

    data = serializers.CharField()
