from rest_framework import serializers
from datetime import timedelta
from schedule.models import LabSchedule


class AvailableTimeSlotSerializer(serializers.Serializer):
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()


class LabScheduleAvailabilitySerializer(serializers.ModelSerializer):
    available_slots = AvailableTimeSlotSerializer(many=True)

    class Meta:
        model = LabSchedule
        fields = ["schedule_date", "available_slots"]
