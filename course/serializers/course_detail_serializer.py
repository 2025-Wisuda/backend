from rest_framework import serializers
from course.models import Course
from course.validators import validate_course_fields
from custom_auth.serializers import UserSimpleSerializer, UserListSerializer
from .course_session_list_serializer import CourseSessionListSerializer
from custom_auth.models import User


class CourseDetailSerializer(serializers.ModelSerializer):
    created_by = UserListSerializer(read_only=True)
    students = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False
    )
    teaching_assistants = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False
    )
    enroll_key = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "start_date",
            "end_date",
            "students",
            "teaching_assistants",
            "sessions",
            "enroll_key",
            "created_by",
            "total_students",
            "total_teaching_assistants",
            "total_participants",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "sessions",
            "created_at",
            "updated_at",
            "total_students",
            "total_teaching_assistants",
            "total_participants",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["students"] = UserSimpleSerializer(instance.students.all(), many=True).data
        data["teaching_assistants"] = UserSimpleSerializer(
            instance.teaching_assistants.all(), many=True
        ).data

        show_sessions = self.context.get("show_sessions", False)
        if show_sessions:
            active_sessions = instance.sessions.filter(is_active=True)
            data["sessions"] = CourseSessionListSerializer(
                active_sessions, many=True, context=self.context
            ).data
        else:
            data["sessions"] = []

        return data

    def validate(self, data):
        return validate_course_fields(data, instance=self.instance)
