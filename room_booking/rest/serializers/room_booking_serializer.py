from django.contrib.auth import get_user_model
from rest_framework import serializers

from core import BookingType, UserGroup

from ...models import RoomBookingModel

User = get_user_model()


class RoomBookingDetailSerializer(serializers.ModelSerializer):
    """
    Complete serializer for room booking detail views with all fields
    """

    booker_name = serializers.CharField(source="booker.get_full_name", read_only=True)
    booker_identifier = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RoomBookingModel
        fields = [
            "id",
            "booker",
            "booker_name",
            "booker_identifier",
            "booking_type",
            "purpose",
            "date",
            "start_time",
            "end_time",
            "seminar_type",
            "research_title",
            "supervisor_main",
            "supervisor_secondary",
            "examiner",
            "document_proof",
            "approval_status",
            "approved_by_user",
            "approval_timestamp",
            "approval_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "booker",
            "booker_name",
            "booker_identifier",
            "approval_status",
            "approved_by_user",
            "approval_timestamp",
            "approval_notes",
            "created_at",
            "updated_at",
        ]

    def get_booker_identifier(self, obj):
        """Get appropriate user identifier based on user group."""
        return obj.get_user_identifier()

    def validate(self, data):
        """
        Apply the same conditional validation logic as the model
        """
        # Get the user (booker) - for create operations, it will be set by the view
        # For update operations, it should already exist on the instance
        booker = data.get("booker")
        if not booker and self.instance:
            booker = self.instance.booker

        booking_type = data.get(
            "booking_type", getattr(self.instance, "booking_type", None)
        )

        if not booking_type:
            raise serializers.ValidationError("Booking type is required")

        # For create operations, we can't validate user permissions here since booker
        # is set by the view after serializer validation. The view will handle this.
        if booker:
            # Check if user can make this type of booking
            user_group = booker.group
            if UserGroup.is_student_group(user_group):
                if booking_type not in BookingType.student_allowed_types():
                    raise serializers.ValidationError(
                        {
                            "booking_type": f"Students and assistants can only create seminar bookings"
                        }
                    )

        # Conditional field validation for seminar bookings
        if booking_type == BookingType.SEMINAR.value:
            required_fields = [
                "research_title",
                "seminar_type",
                "supervisor_main",
                "examiner",
            ]
            missing_fields = []

            for field in required_fields:
                value = data.get(
                    field,
                    getattr(self.instance, field, None) if self.instance else None,
                )
                if not value:
                    missing_fields.append(field)

            if missing_fields:
                error_dict = {}
                for field in missing_fields:
                    if field == "research_title":
                        error_dict[field] = (
                            "Research title is required for seminar bookings"
                        )
                    elif field == "seminar_type":
                        error_dict[field] = (
                            "Seminar type is required for seminar bookings"
                        )
                    elif field == "supervisor_main":
                        error_dict[field] = (
                            "Main supervisor is required for seminar bookings"
                        )
                    elif field == "examiner":
                        error_dict[field] = "Examiner is required for seminar bookings"

                raise serializers.ValidationError(error_dict)

        return data


class RoomBookingListSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for list views with essential fields only
    Optimized for performance in list endpoints - no validation needed
    """

    booker_name = serializers.CharField(source="booker.get_full_name", read_only=True)
    booker_identifier = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RoomBookingModel
        fields = [
            "id",
            "booker_name",
            "booker_identifier",
            "booking_type",
            "seminar_type",
            "research_title",
            "date",
            "start_time",
            "end_time",
            "approval_status",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "booker_name",
            "booking_type",
            "seminar_type",
            "research_title",
            "date",
            "start_time",
            "end_time",
            "approval_status",
            "created_at",
        ]

    def get_booker_identifier(self, obj):
        """Get appropriate user identifier based on user group."""
        return obj.get_user_identifier()


class RoomBookingApprovalSerializer(serializers.ModelSerializer):
    """
    Serializer for approval/rejection actions by technicians
    """

    class Meta:
        model = RoomBookingModel
        fields = ["approval_notes"]

    def validate(self, data):
        approval_notes = data.get("approval_notes")
        
        # approval_notes is optional, but if provided should not be empty
        if approval_notes is not None and not approval_notes.strip():
            raise serializers.ValidationError(
                {
                    "approval_notes": "Approval notes cannot be empty"
                }
            )

        return data
