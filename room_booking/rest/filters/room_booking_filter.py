import django_filters

from core import ApprovalStatus, BookingType

from ...models import RoomBookingModel


class RoomBookingFilter(django_filters.FilterSet):
    """
    Simple filter class for RoomBookingModel
    """

    # Date filtering
    booking_date = django_filters.DateFilter(
        field_name="booking_date",
        help_text="Filter by specific booking date (YYYY-MM-DD)",
    )
    
    # Booking type filtering
    booking_type = django_filters.ChoiceFilter(
        choices=BookingType.choices, help_text="Filter by booking type"
    )

    # Approval status filtering
    booking_approval_status = django_filters.ChoiceFilter(
        field_name="booking_approval_status",
        choices=ApprovalStatus.choices,
        help_text="Filter by approval status",
    )

    class Meta:
        model = RoomBookingModel
        fields = ["booking_date", "booking_type", "booking_approval_status"]
