"""
Serializers for Face Recognition API endpoints.

Provides serializers for face recognition operations that can be
used across different modules.
"""

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

User = get_user_model()


class FaceRecognitionProcessSerializer(serializers.Serializer):
    """Serializer for processing face recognition."""

    image = serializers.ImageField(help_text=_("Face image to process for recognition"))
    context = serializers.JSONField(
        required=False, help_text=_("Additional context for processing (optional)")
    )
    min_confidence = serializers.FloatField(
        required=False,
        min_value=0.0,
        max_value=1.0,
        help_text=_("Minimum confidence threshold (0.0-1.0)"),
    )


class FaceRecognitionResultSerializer(serializers.Serializer):
    """Serializer for face recognition results."""

    success = serializers.BooleanField()
    confidence = serializers.FloatField()
    identified_user = serializers.SerializerMethodField()
    face_data = serializers.JSONField()
    error = serializers.CharField(required=False)

    def get_identified_user(self, obj):
        """Get identified user information."""
        user = obj.get("identified_user")
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "full_name": user.get_full_name(),
                "email": user.email,
            }
        return None


class FaceRegistrationSerializer(serializers.Serializer):
    """Serializer for face registration."""

    user_id = serializers.IntegerField(help_text=_("ID of user to register face for"))
    image = serializers.ImageField(help_text=_("Face image to register"))

    def validate_user_id(self, value):
        """Validate user exists."""
        try:
            User.objects.get(id=value, is_active=True)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError(_("User not found or inactive"))


class FaceVerificationSerializer(serializers.Serializer):
    """Serializer for face verification."""

    user_id = serializers.IntegerField(help_text=_("ID of user to verify against"))
    image = serializers.ImageField(help_text=_("Face image to verify"))

    def validate_user_id(self, value):
        """Validate user exists."""
        try:
            User.objects.get(id=value, is_active=True)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError(_("User not found or inactive"))


class FaceRegistrationResultSerializer(serializers.Serializer):
    """Serializer for face registration results."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    confidence = serializers.FloatField(required=False)
    error = serializers.CharField(required=False)


class FaceVerificationResultSerializer(serializers.Serializer):
    """Serializer for face verification results."""

    success = serializers.BooleanField()
    is_match = serializers.BooleanField()
    verified = serializers.BooleanField()
    confidence = serializers.FloatField(required=False)
    error = serializers.CharField(required=False)


class FaceRecognitionStatsSerializer(serializers.Serializer):
    """Serializer for face recognition statistics."""

    total_users = serializers.IntegerField()
    users_with_face_data = serializers.IntegerField()
    users_without_face_data = serializers.IntegerField()
    face_recognition_adoption_rate = serializers.FloatField()


class UserWithoutFaceDataSerializer(serializers.ModelSerializer):
    """Serializer for users without face recognition data."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "email", "date_joined"]
        read_only_fields = fields
