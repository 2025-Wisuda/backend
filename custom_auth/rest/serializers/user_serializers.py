"""
User API serializers with basic Django validation.

Provides serializers for different user API endpoints with proper validation
using Django's built-in validators for simplicity and reliability.

Key Features:
- Django built-in validation for emails and images
- Read-only field protection for sensitive data
- Optimized field selection for different use cases (list vs detail)
"""

from django.contrib.auth import get_user_model
from django.core.validators import validate_email, validate_image_file_extension
from rest_framework import serializers

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile management.

    Features:
    - Comprehensive field coverage for profile updates
    - Read-only protection for sensitive system fields
    - Django built-in validation for emails and images
    - Image upload handling with basic validation
    """

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "student_number",
            "employee_number",
            "face_image_url",
            "face_uploaded",
            "avatar_url",
            "is_active",
            "is_staff",
            "date_joined",
            "last_login",
            "updated_at",
            "group",
        ]
        read_only_fields = [
            "student_number",
            "employee_number",
            "face_uploaded",
            "is_active",
            "is_staff",
            "date_joined",
            "last_login",
            "group",
        ]

    def validate_email(self, value):
        """
        Validate email using Django's built-in validator.

        Uses Django's standard email validation for consistency
        and reliability.
        """
        if value:
            try:
                validate_email(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return value

    def validate_avatar_url(self, value):
        """
        Validate avatar image using Django's built-in validator.

        Uses Django's validate_image_file_extension for proper image validation.
        """
        if value:
            try:
                validate_image_file_extension(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return value

    def validate_face_image_url(self, value):
        """
        Validate face image using Django's built-in validator.

        Uses Django's validate_image_file_extension for proper image validation.
        """
        if value:
            try:
                validate_image_file_extension(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return value

    def save(self, **kwargs):
        """
        Save the user instance with proper audit trail.

        Handles the updated_by field for audit purposes.
        """
        updated_by = kwargs.pop("updated_by", None)
        instance = super().save(**kwargs)

        if updated_by and hasattr(instance, "updated_by"):
            instance.updated_by = updated_by
            instance.save(update_fields=["updated_by"])

        return instance


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for user list with essential fields.

    Optimized for list endpoints with minimal fields to improve
    performance and reduce payload size for pagination.
    """

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "student_number",
            "employee_number",
            "avatar_url",
            "group",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed user information.

    Provides comprehensive user details for individual user views
    while excluding sensitive information like passwords.
    """

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "student_number",
            "employee_number",
            "is_active",
            "date_joined",
            "last_login",
            "avatar_url",
            "group",
        ]
