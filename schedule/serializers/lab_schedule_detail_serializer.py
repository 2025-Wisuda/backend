from rest_framework import serializers
from schedule.models import LabSchedule
from schedule.validators import validate_lab_schedule_fields
from custom_auth.serializers import UserListSerializer


class LabScheduleDetailSerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(
        source="get_activity_type_display", read_only=True
    )
    created_by = UserListSerializer(read_only=True)
    approval_status = serializers.CharField(read_only=True)
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
            "activity_type_display",
            "created_by",
            "created_at",
            "updated_at",
            "is_active",
            "approval_status",
            "approved_by",
            "approval_time",
        ]

    def validate(self, data):
        return validate_lab_schedule_fields(data, instance=self.instance)
