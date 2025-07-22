"""
Lab schedule serializers for aggregated schedule data.

Key features:
- Read-only access as this is an aggregator model
- Creator name formatting with fallback logic
- Optimized field sets for list vs detail views
- Available time slot calculation for booking assistance
"""

from rest_framework import serializers

from ...models import LabScheduleModel


class LabScheduleDetailSerializer(serializers.ModelSerializer):
    """
    Detailed view of aggregated lab schedules.

    Security features:
    - All fields read-only as this is an aggregator model
    - Creator name formatting with username fallback
    - Full audit trail for administrative tracking
    """

    created_by = serializers.SerializerMethodField()

    def get_created_by(self, obj):
        """Get creator name with fallback logic."""
        user = obj.created_by
        if not user:
            return None

        first = user.first_name or ""
        last = user.last_name or ""

        if first and last:
            return f"{first} {last}"
        elif first:
            return first
        else:
            return user.username

    class Meta:
        model = LabScheduleModel
        fields = [
            "id",
            "date",
            "start_time",
            "end_time",
            "type",
            "detail",
            "created_by",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "date",
            "start_time",
            "end_time",
            "type",
            "detail",
            "created_by",
            "updated_at",
        ]


class AvailableTimeSlotSerializer(serializers.Serializer):
    """Individual available time slot with start and end times."""

    start_time = serializers.CharField(
        max_length=5, help_text="Start time in HH:MM format"
    )
    end_time = serializers.CharField(max_length=5, help_text="End time in HH:MM format")


class LabScheduleListSerializer(serializers.ModelSerializer):
    """Optimized serializer for lab schedule lists with essential fields only."""


    def get_created_by(self, obj):
        user = obj.created_by
        if not user:
            return None

        first = user.first_name or ""
        last = user.last_name or ""

        if first and last:
            return f"{first} {last}"
        elif first:
            return first
        else:
            return user.username

    class Meta:
        model = LabScheduleModel
        fields = [
            "id",
            "date",
            "start_time",
            "end_time",
            "type",
            "detail"
        ]
        read_only_fields = [
            "id",
            "date",
            "start_time",
            "end_time",
            "type",
            "detail"

        ]
