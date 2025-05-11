from rest_framework import serializers
from course.models import Course
from custom_auth.serializers import UserListSerializer


class CourseListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "start_date",
            "end_date",
        ]
