from rest_framework import serializers

from custom_auth.rest.serializers import UserListSerializer

from ...models import LabScheduleModel


class LabScheduleDetailSerializer(serializers.ModelSerializer):
    """
    Detailed read-only serializer for Laboratory Schedule aggregator.

    This serializer provides comprehensive information about laboratory schedule entries
    that are aggregated from multiple source models (LabAllocation, CourseSession, RoomBooking).

    Features:
    - Read-only access to all fields as this is an aggregator model
    - Includes creator name directly as string
    - Provides full audit trail with creation and modification timestamps
    - Contains source model tracking for traceability

    Usage:
    - Ideal for detailed views and administrative interfaces
    - Used in GET /api/lab-schedule/{id}/ endpoints
    - Suitable for data export and reporting functions

    Returns:
        Complete laboratory schedule entry with creator name, timestamps,
        and source model information for comprehensive tracking.
    """

    created_by = serializers.SerializerMethodField()

    def get_created_by(self, obj):
        """Get creator name with fallback logic."""
        user = obj.created_by
        if not user:
            return None

        first = user.first_name or ""
        last = user.last_name or ""

        if first and last:
            return f"{first} {last}"
        elif first:
            return first
        else:
            return user.username

    class Meta:
        model = LabScheduleModel
        fields = [
            "id",
            "schedule_date",
            "start_time",
            "end_time",
            "activity_type",
            "activity_detail",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "schedule_date",
            "start_time",
            "end_time",
            "activity_type",
            "activity_detail",
            "created_by",
            "created_at",
            "updated_at",
        ]


class AvailableTimeSlotSerializer(serializers.Serializer):
    """
    Serializer for individual available time slots.

    Represents a single available time period with start and end times.
    Used as part of the availability response for lab scheduling.
    """

    start_time = serializers.CharField(
        max_length=5, help_text="Start time in HH:MM format"
    )
    end_time = serializers.CharField(max_length=5, help_text="End time in HH:MM format")


class LabScheduleAvailabilitySerializer(serializers.Serializer):
    """
    Serializer for lab schedule availability response.

    Provides available time slots for a specific date, used by the
    availability endpoint to show when lab booking is possible.

    Features:
    - Date-specific availability calculation
    - Available time slots in structured format
    - Ready for mobile app consumption

    Usage:
    - Used in GET /api/lab-schedule/availability/ endpoint
    - Consumed by mobile apps for booking forms
    - Shows gaps between existing bookings

    Returns:
        List of available time slots with start and end times
        formatted for easy consumption by frontend applications.
    """

    date = serializers.DateField(help_text="Date for which availability is requested")
    available_slots = AvailableTimeSlotSerializer(
        many=True, help_text="List of available time slots for the requested date"
    )


class LabScheduleListSerializer(serializers.ModelSerializer):
    """
    Optimized read-only serializer for Laboratory Schedule list views.

    This serializer provides essential laboratory schedule information optimized
    for list displays, mobile applications, and high-performance endpoints.

    Features:
    - Minimal field set for optimal performance
    - Read-only access as aggregator model
    - Includes basic user information for display
    - Focuses on core scheduling details

    Usage:
    - Perfect for list views and mobile app displays
    - Used in GET /api/lab-schedule/ endpoints
    - Ideal for calendar views and schedule overviews
    - Optimized for pagination and filtering

    Returns:
        Essential laboratory schedule information with minimal overhead
        for efficient list rendering and mobile consumption.
    """

    created_by = serializers.SerializerMethodField()

    def get_created_by(self, obj):
        """Get creator name with fallback logic."""
        user = obj.created_by
        if not user:
            return None

        first = user.first_name or ""
        last = user.last_name or ""

        if first and last:
            return f"{first} {last}"
        elif first:
            return first
        else:
            return user.username

    class Meta:
        model = LabScheduleModel
        fields = [
            "id",
            "schedule_date",
            "start_time",
            "end_time",
            "activity_type",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "schedule_date",
            "start_time",
            "end_time",
            "activity_type",
        ]
