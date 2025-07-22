"""
Lab Schedule URLs for lab_schedule Aggregator.

Provides routes for:
- Lab schedule listing and detail views
- Lab availability checking
"""

from rest_framework.routers import SimpleRouter

from ..views import RoomBookingViewSet

app_name = "room_bookings"

router = SimpleRouter(trailing_slash=False)

router.register(r"room-bookings", RoomBookingViewSet, basename="room_bookings")

urlpatterns = router.urls
