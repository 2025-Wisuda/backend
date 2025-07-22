import django_filters

from core import ApprovalStatus, BookingType

from ...models import RoomBookingModel


class RoomBookingFilter(django_filters.FilterSet):
    """
    Simple filter class for RoomBookingModel
    """

    # Date filtering
    date = django_filters.DateFilter(
        field_name="date",
        help_text="Filter by specific booking date (YYYY-MM-DD)",
    )

    # Booking type filtering
    booking_type = django_filters.ChoiceFilter(
        choices=BookingType.choices, help_text="Filter by booking type"
    )

    # Approval status filtering
    approval_status = django_filters.ChoiceFilter(
        field_name="approval_status",
        choices=ApprovalStatus.choices,
        help_text="Filter by approval status",
    )

    class Meta:
        model = RoomBookingModel
        fields = ["date", "booking_type", "approval_status"]
