"""
Serializers for Guest Visit API endpoints.

Provides serialization for guest visit CRUD operations with
conditional field handling for manual vs registered visitor modes.
"""

from core import VisitorIdentityType
from custom_auth.rest.serializers import UserListSerializer
from rest_framework import serializers

from ...models import GuestVisitModel


class GuestVisitListSerializer(serializers.ModelSerializer):
    """
    Serializer for guest visit list view.

    Provides essential information for list display with
    computed visitor information.
    """

    name_display = serializers.SerializerMethodField()
    identity_display = serializers.SerializerMethodField()

    class Meta:
        model = GuestVisitModel
        fields = [
            "id",
            "name_display",
            "identity_display",
            "date",
            "start_time",
            "end_time",
            "purpose",
            "created_at",
        ]

    def get_name_display(self, obj):
        """Get display name for visitor."""
        return obj.get_visitor_name()

    def get_identity_display(self, obj):
        """Get display identity for visitor."""
        return obj.get_visitor_identity()


class GuestVisitDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for guest visit detail/create/update operations.

    Handles both manual visitor entry and registered user selection
    with proper validation for conditional fields.
    """

    name_display = serializers.SerializerMethodField(read_only=True)
    identity_display = serializers.SerializerMethodField(read_only=True)
    can_edit = serializers.SerializerMethodField(read_only=True)
    created_by = UserListSerializer(source="created_by", read_only=True)

    class Meta:
        model = GuestVisitModel
        fields = [
            "id",
            "visitor",
            "name",
            "identity_type",
            "identity_number",
            "name_display",
            "identity_display",
            "date",
            "start_time",
            "end_time",
            "purpose",
            "paraf",
            "staff",
            "can_edit",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def get_name_display(self, obj):
        """Get display name for visitor."""
        return obj.get_visitor_name()

    def get_identity_display(self, obj):
        """Get display identity for visitor."""
        return obj.get_visitor_identity()

    def get_can_edit(self, obj):
        """Check if visit can still be edited."""
        return obj.can_edit()

    def validate(self, data):
        """Validate guest visit data."""
        visitor = data.get("visitor")
        name = data.get("name")
        identity_type = data.get("identity_type")
        identity_number = data.get("identity_number")

        # Either visitor OR manual name must be provided
        if not visitor and not name:
            raise serializers.ValidationError(
                {"name": "Either select a registered user or provide visitor name"}
            )

        # If manual entry, identity fields should be provided together
        if not visitor:
            if identity_type and not identity_number:
                raise serializers.ValidationError(
                    {
                        "identity_number": "Identity number required when identity type is selected"
                    }
                )
            if identity_number and not identity_type:
                raise serializers.ValidationError(
                    {
                        "identity_type": "Identity type required when identity number is provided"
                    }
                )

        return data
