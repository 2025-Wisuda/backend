"""
Serializers for DutyAttendanceModel with tracking with clock in/out functionality.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from shared.services.duty_otp_service import DutyOTPService

from ...models import DutyAttendanceModel


class DutyAttendancePersonalSerializer(serializers.ModelSerializer):
    """Simple personal attendance serializer for /me endpoint."""

    duty_start_time = serializers.TimeField(
        source="duty_schedule.duty_start_time", read_only=True
    )
    duty_end_time = serializers.TimeField(
        source="duty_schedule.duty_end_time", read_only=True
    )

    class Meta:
        model = DutyAttendanceModel
        fields = [
            "id",
            "duty_date",
            "duty_start_time",
            "duty_end_time",
            "clock_in_time",
            "clock_out_time",
            "attendance_status",
        ]
        read_only_fields = [
            "id",
            "duty_date",
            "duty_start_time",
            "duty_end_time",
            "clock_in_time",
            "clock_out_time",
            "attendance_status",
        ]


class DutyAttendanceListSerializer(serializers.ModelSerializer):
    """Admin list - attendance records grouped by date with assistant array."""

    laboratory_assistant = serializers.SerializerMethodField()

    class Meta:
        model = DutyAttendanceModel
        fields = [
            "duty_date",
            "laboratory_assistant",
        ]
        read_only_fields = [
            "duty_date",
            "laboratory_assistant",
        ]

    def get_laboratory_assistant(self, obj):
        """Get assistant info with attendance status."""
        user = obj.duty_assistant
        if not user:
            return []

        # Get assistant name
        first = user.first_name or ""
        last = user.last_name or ""

        if first and last:
            name = f"{first} {last}"
        elif first:
            name = first
        else:
            name = user.username

        return [
            {
                "name": name,
                "student_number": user.student_number or "",
                "attendance_status": obj.attendance_status,
            }
        ]


class DutyAttendanceDetailSerializer(serializers.ModelSerializer):
    """Admin detail view - attendance record with assistant info and clock times."""

    laboratory_assistant = serializers.SerializerMethodField()

    class Meta:
        model = DutyAttendanceModel
        fields = [
            "duty_date",
            "laboratory_assistant",
        ]
        read_only_fields = [
            "duty_date",
            "laboratory_assistant",
        ]

    def get_laboratory_assistant(self, obj):
        """Get assistant info with attendance status and clock times."""
        user = obj.duty_assistant
        if not user:
            return []

        # Get assistant name
        first = user.first_name or ""
        last = user.last_name or ""

        if first and last:
            name = f"{first} {last}"
        elif first:
            name = first
        else:
            name = user.username

        return [
            {
                "name": name,
                "student_number": user.student_number or "",
                "attendance_status": obj.attendance_status,
                "clock_in_time": obj.clock_in_time,
                "clock_out_time": obj.clock_out_time,
            }
        ]


class DutyOTPSerializer(serializers.Serializer):
    """Serializer for OTP validation - separate from clock in/out."""

    otp_code = serializers.CharField(
        max_length=6,
        min_length=6,
        required=True,
        help_text=_("6-digit OTP code for verification"),
    )

    def validate_otp_code(self, value):
        """Validate the OTP code."""
        if not value or not value.isdigit():
            raise serializers.ValidationError(_("OTP must be a 6-digit number."))

        # Get user from context
        request = self.context.get("request")
        user_id = str(request.user.id) if request and request.user else None

        # Validate OTP
        is_valid, error_message = DutyOTPService.validate_otp(
            otp_code=value, user_id=user_id
        )

        if not is_valid:
            raise serializers.ValidationError(error_message)

        return value


class DutyAttendanceClockInSerializer(serializers.Serializer):
    """Simple serializer for manual clock-in process."""

    notes = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text=_("Optional notes for clock-in"),
    )

    latitude = serializers.FloatField(
        required=False,
        min_value=-90,
        max_value=90,
        help_text=_("Optional latitude coordinate"),
    )

    longitude = serializers.FloatField(
        required=False,
        min_value=-180,
        max_value=180,
        help_text=_("Optional longitude coordinate"),
    )


class DutyAttendanceClockOutSerializer(serializers.Serializer):
    """Simple serializer for manual clock-out process."""

    notes = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text=_("Optional notes for clock-out"),
    )

    latitude = serializers.FloatField(
        required=False,
        min_value=-90,
        max_value=90,
        help_text=_("Optional latitude coordinate"),
    )

    longitude = serializers.FloatField(
        required=False,
        min_value=-180,
        max_value=180,
        help_text=_("Optional longitude coordinate"),
    )
