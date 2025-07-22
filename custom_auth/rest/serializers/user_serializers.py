"""
User Serializers

Serializers for user data operations with role-based field access control.
Provides different serialization levels for list, detail, and profile views.
"""

from django.contrib.auth import get_user_model
from django.core.validators import validate_email, validate_image_file_extension
from rest_framework import serializers

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile operations (self-management).

    Features:
    - Read-only fields for sensitive data (group, staff status, ID numbers)
    - Image validation for avatar field
    - Email validation
    - Audit trail support
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
            "avatar",
            "is_staff",
            "date_joined",
            "last_login",
            "updated_at",
            "group",
        ]
        read_only_fields = [
            "student_number",
            "employee_number",
            "is_staff",
            "date_joined",
            "last_login",
            "group",
        ]

    def validate_email(self, value):
        if value:
            try:
                validate_email(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return value

    def validate_avatar(self, value):
        if value:
            try:
                validate_image_file_extension(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return value

    def save(self, **kwargs):
        updated_by = kwargs.pop("updated_by", None)
        instance = super().save(**kwargs)

        if updated_by and hasattr(instance, "updated_by"):
            instance.updated_by = updated_by
            instance.save(update_fields=["updated_by"])

        return instance


class UserListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for user list views.

    Includes essential fields for listing and search operations.
    Optimized for performance with minimal field set.
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
            "avatar",
            "group",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for user detail views.

    Includes extended user information for detailed inspection.
    Used by admin and detail endpoints.
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
            "date_joined",
            "last_login",
            "avatar",
            "group",
        ]
