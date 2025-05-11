from rest_framework import serializers
from course.models import Course


def validate_course_fields(data, instance=None):
    start_date = (
        data.get("start_date")
        if "start_date" in data
        else (instance.start_date if instance else None)
    )
    end_date = (
        data.get("end_date")
        if "end_date" in data
        else (instance.end_date if instance else None)
    )

    if start_date and end_date and end_date < start_date:
        raise serializers.ValidationError(
            "End date must be after or equal to start date."
        )

    title = data.get("title", instance.title if instance else "").strip()
    description = data.get("description", instance.description if instance else "")
    is_active = data.get("is_active", instance.is_active if instance else True)

    if not title:
        raise serializers.ValidationError(
            "Course title cannot be empty or only spaces."
        )

    if is_active:
        existing_course = (
            Course.objects.filter(title=title, is_active=True)
            .exclude(id=instance.id if instance else None)
            .first()
        )
        if existing_course:
            raise serializers.ValidationError(
                "A course with this title already exists."
            )

    if description and len(description) > 500:
        raise serializers.ValidationError("Description cannot exceed 500 characters.")

    return data
