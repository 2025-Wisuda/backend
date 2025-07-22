"""
FCM Device Serializer
"""

from rest_framework import serializers

from ...models import FCMDeviceModel


class FCMDeviceSerializer(serializers.ModelSerializer):
    """Serializer for FCM Device Model"""

    class Meta:
        model = FCMDeviceModel
        fields = [
            "id",
            "registration_token",
            "device_type",
            "device_name",
            "is_active",
            "last_used",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_used", "created_at", "updated_at"]

class RegisterDeviceResponseSerializer(serializers.Serializer):
    device_id = serializers.IntegerField()


class SendTestNotificationResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
