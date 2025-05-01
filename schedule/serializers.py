from rest_framework import serializers
from .models import LabSchedule
from datetime import datetime


class LabScheduleDetailSerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(
        source="get_activity_type_display", read_only=True
    )
    approval_status = serializers.CharField(read_only=True)
    approved_by = serializers.StringRelatedField(read_only=True)
    approval_time = serializers.DateTimeField(read_only=True)

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
        start_time = (
            data.get("start_time")
            if "start_time" in data
            else (self.instance.start_time if self.instance else None)
        )
        end_time = (
            data.get("end_time")
            if "end_time" in data
            else (self.instance.end_time if self.instance else None)
        )
        schedule_date = (
            data.get("schedule_date")
            if "schedule_date" in data
            else (self.instance.schedule_date if self.instance else None)
        )

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError("End time must be after start time.")

        if schedule_date and start_time:
            combined_datetime = datetime.combine(schedule_date, start_time)
            if combined_datetime < datetime.now():
                raise serializers.ValidationError(
                    "Schedule date must be in the future."
                )

        if schedule_date and start_time and end_time:
            overlapping_schedule = LabSchedule.objects.filter(
                schedule_date=schedule_date, is_active=True
            ).filter(start_time__lt=end_time, end_time__gt=start_time)

            if overlapping_schedule.exists():
                raise serializers.ValidationError(
                    "The new schedule overlaps with an existing schedule."
                )

        return data


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
            "created_by",
            "approval_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["activity_type_display"]


class LabScheduleApprovalSerializer(serializers.ModelSerializer):
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
