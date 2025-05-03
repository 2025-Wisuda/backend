from rest_framework import serializers
from schedule.models import DutySchedule
from custom_auth.serializers import UserListSerializer


class DutyScheduleListSerializer(serializers.ModelSerializer):
    days_display = serializers.CharField(source="days", read_only=True)
    teaching_assistants = UserListSerializer(many=True, read_only=True)

    class Meta:
        model = DutySchedule
        fields = [
            "id",
            "days_display",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "teaching_assistants",
            "created_at",
            "updated_at",
        ]
