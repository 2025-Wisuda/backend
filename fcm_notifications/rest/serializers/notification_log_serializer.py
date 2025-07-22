"""
Notification Log Serializer - Clean version only
"""

from rest_framework import serializers

from ...models import NotificationLogModel


class NotificationLogListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing notifications"""

    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = NotificationLogModel
        fields = [
            "id",
            "user_name",
            "notification_type",
            "title",
            "body",
            "sent_at",
            "status",
            "is_read",
        ]
        read_only_fields = fields


class NotificationMarkAsReadResponseSerializer(serializers.Serializer):
    id = serializers.CharField()


class NotificationMarkAllAsReadResponseSerializer(serializers.Serializer):
    updated_count = serializers.IntegerField()


class NotificationUnreadCountResponseSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()
