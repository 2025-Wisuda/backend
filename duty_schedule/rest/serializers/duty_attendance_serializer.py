"""
Serializers for DutyAttendanceModel with tracking with clock in/out functionality.
"""

from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from shared.services.duty_otp_service import DutyOTPService

from ...models import DutyAttendanceModel


class DutyAttendancePersonalSerializer(serializers.ModelSerializer):
    """Simple personal attendance serializer for /me endpoint."""

    class Meta:
        model = DutyAttendanceModel
        fields = [
            "id",
            "date",
            "clock_in_time",
            "clock_out_time",
            "status",
        ]
        read_only_fields = [
            "id",
            "date",
            "clock_in_time",
            "clock_out_time",
            "status",
        ]


class DutyAttendanceListSerializer(serializers.ModelSerializer):
    """Admin list - better structure with grouped assistants by date."""

    laboratory_assistant = serializers.SerializerMethodField()

    class Meta:
        model = DutyAttendanceModel
        fields = [
            "id",
            "date",
            "status",
            "clock_in_time",
            "clock_out_time",
            "laboratory_assistant",
        ]
        read_only_fields = fields

    def get_laboratory_assistant(self, obj):
        user = obj.laboratory_assistant
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


class DutyAttendanceDetailSerializer(serializers.ModelSerializer):
    """Admin detail view - attendance record with assistant info and clock times."""

    laboratory_assistant = serializers.SerializerMethodField()

    class Meta:
        model = DutyAttendanceModel
        fields = [
            "id",
            "date",
            "start_time",
            "end_time",
            "clock_in_time",
            "clock_out_time",
            "status",
            "otp_validated_at",
            "face_recognition_confidence",
            "manual_clock_in_override",
            "manual_clock_out_override",
            "laboratory_assistant",
        ]
        read_only_fields = [
            "id",
            "date",
            "start_time",
            "end_time",
            "clock_in_time",
            "clock_out_time",
            "status",
            "otp_validated_at",
            "face_recognition_confidence",
            "manual_clock_in_override",
            "manual_clock_out_override",
            "laboratory_assistant",
        ]

    def get_laboratory_assistant(self, obj):
        """Get assistant info with attendance status and clock times."""
        user = obj.laboratory_assistant
        if not user:
            return None

        # Get assistant name
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
        user_id = str(request.user.id) if request and request.user else ""

        # Validate OTP
        is_valid, error_message = DutyOTPService.validate_otp(
            otp_code=value, user_id=user_id
        )

        if not is_valid:
            raise serializers.ValidationError(error_message)

        return value


class DutyAttendanceClockInSerializer(serializers.ModelSerializer):
    """Serializer for clock-in process - manual mode without face recognition."""

    class Meta:
        model = DutyAttendanceModel
        fields = []


class DutyAttendanceClockOutSerializer(serializers.ModelSerializer):
    """Serializer for clock-out process - manual mode without face recognition."""

    class Meta:
        model = DutyAttendanceModel
        fields = []


class DutyAttendanceWebSocketSerializer(serializers.ModelSerializer):
    """Serializer for WebSocket attendance responses."""

    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    confidence = serializers.SerializerMethodField()
    manual_override = serializers.SerializerMethodField()

    class Meta:
        model = DutyAttendanceModel
        fields = [
            "id",
            "date",
            "start_time",
            "end_time",
            "clock_in_time",
            "clock_out_time",
            "status",
            "confidence",
            "manual_override",
        ]

    def get_start_time(self, obj):
        return obj.start_time.strftime("%H:%M") if obj.start_time else None

    def get_end_time(self, obj):
        return obj.end_time.strftime("%H:%M") if obj.end_time else None

    def get_confidence(self, obj):
        return obj.get_confidence_percentage()

    def get_manual_override(self, obj):
        return obj.manual_clock_in_override or obj.manual_clock_out_override


class DutyAttendanceStatisticsSerializer(serializers.Serializer):
    """Serializer for attendance statistics response."""

    summary = serializers.SerializerMethodField()
    status_breakdown = serializers.SerializerMethodField()
    daily_trends = serializers.SerializerMethodField()
    assistant_performance = serializers.SerializerMethodField()
    filters = serializers.SerializerMethodField()

    def get_summary(self, obj):
        queryset = obj.get("queryset")
        start_date = obj.get("start_date")
        end_date = obj.get("end_date")
        daily_trends = obj.get("daily_trends")

        total_duties = queryset.count()
        overall_rate = round(
            (
                (sum(item["present"] for item in daily_trends) / total_duties * 100)
                if total_duties > 0
                else 0
            ),
            1,
        )

        return {
            "total_duties": total_duties,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_count": (end_date - start_date).days + 1,
            },
            "overall_attendance_rate": overall_rate,
        }

    def get_status_breakdown(self, obj):
        queryset = obj.get("queryset")
        status_breakdown = (
            queryset.values("status").annotate(count=Count("id")).order_by("status")
        )
        total_duties = queryset.count()

        return [
            {
                "status": item["status"],
                "count": item["count"],
                "percentage": round(
                    (item["count"] / total_duties * 100) if total_duties > 0 else 0, 1
                ),
            }
            for item in status_breakdown
        ]

    def get_daily_trends(self, obj):
        daily_trends = obj.get("daily_trends")
        return [
            {
                "date": item["date"].isoformat(),
                "total": item["total"],
                "present": item["present"],
                "absent": item["absent"],
                "late": item["late"],
                "attendance_rate": round(
                    (item["present"] / item["total"] * 100) if item["total"] > 0 else 0,
                    1,
                ),
            }
            for item in daily_trends
        ]

    def get_assistant_performance(self, obj):
        assistant_stats = obj.get("assistant_stats", [])
        return [
            {
                "assistant_id": item["laboratory_assistant__id"],
                "name": f"{item['laboratory_assistant__first_name']} {item['laboratory_assistant__last_name']}".strip()
                or item["laboratory_assistant__username"],
                "username": item["laboratory_assistant__username"],
                "total_duties": item["total_duties"],
                "present_count": item["present_count"],
                "absent_count": item["absent_count"],
                "late_count": item["late_count"],
                "attendance_rate": round(
                    (
                        (item["present_count"] / item["total_duties"] * 100)
                        if item["total_duties"] > 0
                        else 0
                    ),
                    1,
                ),
            }
            for item in assistant_stats
        ]

    def get_filters(self, obj):
        return {
            "start_date": obj.get("start_date").isoformat(),
            "end_date": obj.get("end_date").isoformat(),
            "assistant_id": obj.get("assistant_id"),
        }


class DutyAttendanceStatusBreakdownSerializer(serializers.Serializer):
    """Serializer for status breakdown data."""

    status = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class DutyAttendanceDailyTrendSerializer(serializers.Serializer):
    """Serializer for daily attendance trends."""

    date = serializers.CharField()
    total = serializers.IntegerField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    late = serializers.IntegerField()
    attendance_rate = serializers.FloatField()


class DutyAttendanceAssistantPerformanceSerializer(serializers.Serializer):
    """Serializer for assistant performance data."""

    assistant_id = serializers.CharField()
    name = serializers.CharField()
    username = serializers.CharField()
    total_duties = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    attendance_rate = serializers.FloatField()


class DutyAttendanceSummarySerializer(serializers.Serializer):
    """Serializer for summary statistics."""

    total_duties = serializers.IntegerField()
    date_range = serializers.DictField()
    overall_attendance_rate = serializers.FloatField()


class DutyAttendanceManualOverrideSerializer(serializers.Serializer):
    """Serializer for manual override response."""

    attendance = DutyAttendanceDetailSerializer()
    override = serializers.SerializerMethodField()

    def get_override(self, obj):
        return {
            "action": obj.get("action"),
            "status": obj.get("status"),
            "overridden_by": obj.get("overridden_by"),
        }
