from rest_framework import serializers
from schedule.models import DutySchedule
from custom_auth.serializers import UserListSerializer
from .duty_date_nested_serializer import DutyDateNestedSerializer
from schedule.validators import validate_duty_schedule_fields


class DutyScheduleDetailSerializer(serializers.ModelSerializer):
    days_display = serializers.CharField(source="days", read_only=True)
    duty_dates = DutyDateNestedSerializer(many=True, read_only=True)
    teaching_assistants = UserListSerializer(many=True, read_only=True)

    class Meta:
        model = DutySchedule
        fields = [
            "id",
            "days",
            "days_display",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "duty_dates",
            "teaching_assistants",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "days_display",
            "duty_dates",
            "teaching_assistants",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        return validate_duty_schedule_fields(data, self.instance)
