from rest_framework import serializers
from .models import LabSchedule


class LabScheduleDetailSerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(
        source="get_activity_type_display", read_only=True
    )

    class Meta:
        model = LabSchedule
        fields = [
            "id",
            "activity_type",
            "activity_type_display",
            "activity_description",
            "schedule_date",
            "start_time",
            "end_time",
            "created_by",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "activity_type_display",
            "created_by",
            "created_at",
            "updated_at",
        ]


class LabScheduleListSerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(
        source="get_activity_type_display", read_only=True
    )

    class Meta:
        model = LabSchedule
        fields = [
            "id",
            "activity_type_display",
            "activity_description",
            "schedule_date",
            "start_time",
            "end_time",
        ]
        read_only_fields = ["activity_type_display"]
