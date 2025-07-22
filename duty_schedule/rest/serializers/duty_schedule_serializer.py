"""
Serializer for Duty Schedule.
This serializer is used to represent duty schedule records in different formats.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from ...models import DutyScheduleModel


class DutyScheduleSerializer(serializers.Serializer):
    """General Duty Schedule Serializer - just schedule info without attendance status."""

    def to_representation(self, instance):
        """Return dictionary with assistants array."""
        # Get all assistants assigned to this duty schedule
        assistants = instance.laboratory_assistants.all()
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

            # Get avatar URL
            avatar_url = None
            if assistant.avatar:
                request = self.context.get("request")
                if request:
                    avatar_url = request.build_absolute_uri(assistant.avatar.url)
                else:
                    avatar_url = assistant.avatar.url

            assistant_list.append(
                {
                    "name": name,
                    "student_number": getattr(assistant, "student_number", "")
                    or assistant.username,
                    "avatar": avatar_url,
                }
            )

        return {
            "assistants": assistant_list,
            "days": instance.days
        }


class DutyScheduleTodaySerializer(serializers.Serializer):
    """Today's Duty Schedule Serializer - with attendance status for today only."""

    def to_representation(self, instance):
        """Return array of assistants with attendance status for today."""
        from datetime import date

        from ...models import DutyAttendanceModel

        # Get target date from context or use today
        target_date = self.context.get("date", date.today())

        # Get all assistants assigned to this duty schedule
        assistants = instance.laboratory_assistants.all()
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
                    duty_schedule=instance,
                    laboratory_assistant=assistant,
                    date=target_date,
                    is_active=True,
                )
                status = attendance.status
            except DutyAttendanceModel.DoesNotExist:
                status = "No Record"

            # Get avatar URL
            avatar_url = None
            if assistant.avatar:
                request = self.context.get("request")
                if request:
                    avatar_url = request.build_absolute_uri(assistant.avatar.url)
                else:
                    avatar_url = assistant.avatar.url

            assistant_list.append(
                {
                    "name": name,
                    "student_number": getattr(assistant, "student_number", "")
                    or assistant.username,
                    "status": status,
                    "avatar": avatar_url,
                }
            )

        return assistant_list