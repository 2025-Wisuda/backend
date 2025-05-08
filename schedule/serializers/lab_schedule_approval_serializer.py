from rest_framework import serializers
from schedule.models import LabSchedule
from custom_auth.serializers import UserListSerializer


class LabScheduleApprovalSerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(
        source="get_activity_type_display", read_only=True
    )
    created_by = UserListSerializer(read_only=True)
    approved_by = UserListSerializer(read_only=True)

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
            "approval_status",
            "approved_by",
            "approval_time",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "activity_type",
            "activity_type_display",
            "activity_description",
            "schedule_date",
            "start_time",
            "end_time",
            "created_by",
            "is_active",
            "approved_by",
            "approval_time",
            "created_at",
            "updated_at",
        ]
