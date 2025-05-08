from datetime import datetime, time, date
from rest_framework import serializers


def validate_duty_schedule_fields(data, instance=None):
    start_time = data.get("start_time") or (instance.start_time if instance else None)
    end_time = data.get("end_time") or (instance.end_time if instance else None)
    start_date = data.get("start_date") or (instance.start_date if instance else None)
    end_date = data.get("end_date") or (instance.end_date if instance else None)
    
    min_time = time(7, 30)
    max_time = time(18, 0)
    
    if start_time and (start_time < min_time or start_time > max_time):
        raise serializers.ValidationError("Start time must be between 07:30 and 18:00.")
    if end_time and (end_time < min_time or end_time > max_time):
        raise serializers.ValidationError("End time must be between 07:30 and 18:00.")
    if start_time and end_time and end_time <= start_time:
        raise serializers.ValidationError("End time must be after start time.")

    if start_date and end_date and end_date < start_date:
        raise serializers.ValidationError("End date must be after start date.")

    if start_date and start_time:
        combined_datetime = datetime.combine(start_date, start_time)
        if combined_datetime < datetime.now():
            raise serializers.ValidationError(
                "Start date and time must be in the future."
            )

    return data
