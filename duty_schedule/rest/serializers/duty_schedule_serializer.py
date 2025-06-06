"""
Serializer for Duty Attendance List.
This serializer is used to represent duty attendance records in a public format,
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from ...models import DutyScheduleModel


class DutyScheduleSerializer(serializers.ModelSerializer):
    """General Duty Schedule Serializer - without attendance status."""

    laboratory_assistant = serializers.SerializerMethodField()

    class Meta:
        model = DutyScheduleModel
        fields = ["duty_days", "laboratory_assistant"]
        read_only_fields = ["duty_days", "laboratory_assistant"]

    def get_laboratory_assistant(self, obj):
        """Get list of assigned laboratory assistants names and student numbers only."""
        assistants = obj.duty_assistants.all()
        assistant_list = []

        for assistant in assistants:
            # Get assistant name
            first = assistant.first_name or ""
            last = assistant.last_name or ""

            if first and last:
                name = f"{first} {last}"
            elif first:
                name = first
            else:
                name = assistant.username

            assistant_list.append(
                {
                    "name": name,
                    "student_number": getattr(assistant, "student_number", "")
                    or assistant.username,
                }
            )

        return assistant_list


class DutyScheduleTodaySerializer(serializers.ModelSerializer):
    """Today's Duty Schedule Serializer - with attendance status only."""

    laboratory_assistant = serializers.SerializerMethodField()

    class Meta:
        model = DutyScheduleModel
        fields = ["laboratory_assistant"]
        read_only_fields = ["laboratory_assistant"]

    def get_laboratory_assistant(self, obj):
        """Get list of assigned laboratory assistants with their names and duty status."""
        from datetime import date

        from core.enums import AttendanceStatus

        from ...models import DutyAttendanceModel

        # Get target date from context or use today
        target_date = self.context.get("date", date.today())

        # Get all assistants assigned to this duty schedule
        assistants = obj.duty_assistants.all()
        assistant_list = []

        for assistant in assistants:
            # Get assistant name
            first = assistant.first_name or ""
            last = assistant.last_name or ""

            if first and last:
                name = f"{first} {last}"
            elif first:
                name = first
            else:
                name = assistant.username

            # Get attendance status for this assistant on target date
            try:
                attendance = DutyAttendanceModel.objects.get(
                    duty_schedule=obj,
                    duty_assistant=assistant,
                    duty_date=target_date,
                    is_active=True,
                )
                duty_status = attendance.attendance_status
            except DutyAttendanceModel.DoesNotExist:
                duty_status = "No Record"

            assistant_list.append(
                {
                    "name": name,
                    "student_number": getattr(assistant, "student_number", "")
                    or assistant.username,
                    "duty_status": duty_status,
                }
            )

        return assistant_list
