from rest_framework import serializers
from course.models import CourseSession
from custom_auth.serializers import UserListSerializer, UserSimpleSerializer
from course.serializers.course_list_serializer import CourseListSerializer
from schedule.models import LabSchedule
from custom_auth.models import User
from course.models import Course
from datetime import datetime


class CourseSessionDetailSerializer(serializers.ModelSerializer):
    created_by = UserListSerializer(read_only=True)
    teaching_assistants = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False
    )
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())

    approval_status = serializers.CharField(
        source="lab_schedule.approval_status", read_only=True
    )
    approval_time = serializers.DateTimeField(
        source="lab_schedule.approval_time", read_only=True
    )
    approved_by = UserListSerializer(source="lab_schedule.approved_by", read_only=True)

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
            "created_by",
            "teaching_assistants",
            "approval_status",
            "approval_time",
            "approved_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_by",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["course"] = CourseListSerializer(instance.course).data
        data["teaching_assistants"] = UserSimpleSerializer(
            instance.teaching_assistants.all(), many=True
        ).data
        return data
