from rest_framework import serializers
from schedule.models import LabSchedule
from datetime import datetime
from datetime import time


def validate_lab_schedule_fields(data, instance=None):
    start_time = (
        data.get("start_time")
        if "start_time" in data
        else (instance.start_time if instance else None)
    )
    end_time = (
        data.get("end_time")
        if "end_time" in data
        else (instance.end_time if instance else None)
    )
    schedule_date = (
        data.get("schedule_date")
        if "schedule_date" in data
        else (instance.schedule_date if instance else None)
    )

    min_time = time(7, 30)
    max_time = time(18, 0)
    if start_time and (start_time < min_time or start_time > max_time):
        raise serializers.ValidationError("Start time must be between 07:30 and 18:00.")
    if end_time and (end_time < min_time or end_time > max_time):
        raise serializers.ValidationError("End time must be between 07:30 and 18:00.")

    if start_time and end_time and end_time <= start_time:
        raise serializers.ValidationError("End time must be after start time.")

    if schedule_date and start_time:
        combined_datetime = datetime.combine(schedule_date, start_time)
        if combined_datetime < datetime.now():
            raise serializers.ValidationError("Schedule date must be in the future.")

    if schedule_date and start_time and end_time:
        start_dt = datetime.combine(schedule_date, start_time)
        end_dt = datetime.combine(schedule_date, end_time)

        overlapping_schedule = LabSchedule.objects.filter(
            schedule_date=schedule_date,
            is_active=True,
        ).exclude(id=instance.id if instance else None)

        for schedule in overlapping_schedule:
            existing_start = datetime.combine(
                schedule.schedule_date, schedule.start_time
            )
            existing_end = datetime.combine(schedule.schedule_date, schedule.end_time)

            if (start_dt < existing_end) and (end_dt > existing_start):
                raise serializers.ValidationError(
                    "The new schedule overlaps with an existing schedule."
                )

    return data
