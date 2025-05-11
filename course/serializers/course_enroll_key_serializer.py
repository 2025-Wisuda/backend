from rest_framework import serializers


class CourseEnrollKeySerializer(serializers.Serializer):
    enroll_key = serializers.CharField()
