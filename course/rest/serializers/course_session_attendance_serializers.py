"""Course Session Attendance Serializers - Setara dengan DutyAttendance."""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from ...models import CourseSessionAttendanceModel


class CourseSessionAttendancePersonalSerializer(serializers.ModelSerializer):
    """Simple personal attendance serializer for /me endpoint."""

    marked_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CourseSessionAttendanceModel
        fields = [
            "status",
            "marked_at",
            "marked_by_name",
            "face_recognition_confidence",
        ]
        read_only_fields = fields

    def get_marked_by_name(self, obj):
        if not obj.marked_by:
            return None
        return self.get_full_name(obj.marked_by)

    def get_full_name(self, user):
        if user.first_name and user.last_name:
            return f"{user.first_name} {user.last_name}"
        elif user.first_name:
            return user.first_name
        elif user.last_name:
            return user.last_name
        return user.username


class CourseSessionAttendanceListSerializer(serializers.ModelSerializer):
    """List serializer - with student info."""

    student = serializers.SerializerMethodField()

    class Meta:
        model = CourseSessionAttendanceModel
        fields = [
            "id",
            "student",
            "status",
            "marked_at",
            "manual_attendance_override",
        ]
        read_only_fields = fields

    def get_student(self, obj):
        user = obj.student
        if not user:
            return None
        first = user.first_name or ""
        last = user.last_name or ""
        if first and last:
            name = f"{first} {last}"
        elif first:
            name = first
        else:
            name = user.username
        return {
            "name": name,
            "student_number": user.student_number or "",
        }






class CourseSessionAttendanceDetailSerializer(serializers.ModelSerializer):
    """Detail serializer - with full info, flat student fields."""

    student = serializers.SerializerMethodField()
    marked_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CourseSessionAttendanceModel
        fields = [
            "id",
            "student",
            "status",
            "marked_at",
            "marked_by_name",
            "manual_attendance_override",
            "face_recognition_confidence",
        ]
        read_only_fields = fields

    def get_student(self, obj):
        user = obj.student
        if not user:
            return None
        first = user.first_name or ""
        last = user.last_name or ""
        if first and last:
            name = f"{first} {last}"
        elif first:
            name = first
        else:
            name = user.username
        return {
            "name": name,
            "student_number": user.student_number or "",
        }

    def get_marked_by_name(self, obj):
        if not obj.marked_by:
            return None
        return self.get_full_name(obj.marked_by)

    def get_full_name(self, user):
        if user.first_name and user.last_name:
            return f"{user.first_name} {user.last_name}"
        elif user.first_name:
            return user.first_name
        elif user.last_name:
            return user.last_name
        return user.username


class CourseSessionAttendanceManualOverrideSerializer(serializers.Serializer):
    """Serializer for manual override response."""

    attendance = CourseSessionAttendanceDetailSerializer()
    override = serializers.SerializerMethodField()

    def get_override(self, obj):
        return {
            "status": obj.get("status"),
            "marked_by": obj.get("marked_by"),
            "marked_at": obj.get("marked_at"),
        }
