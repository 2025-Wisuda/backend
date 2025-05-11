from rest_framework import serializers
from course.models import CourseSession, Course
from custom_auth.models import User
from custom_auth.serializers import UserSimpleSerializer


class CourseSessionListSerializer(serializers.ModelSerializer):
    teaching_assistants = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False
    )

    class Meta:
        model = CourseSession
        fields = [
            "id",
            "title",
            "course",
            "session_date",
            "start_time",
            "end_time",
            "status",
            "teaching_assistants",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["course"] = instance.course.title
        data["teaching_assistants"] = UserSimpleSerializer(
            instance.teaching_assistants.all(), many=True
        ).data
        return data
