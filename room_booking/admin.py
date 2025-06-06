"""Expose selected admin components for external use."""

from .admins.room_booking_admin import RoomBookingAdmin
from .admins.room_booking_resource import RoomBookingResource

__all__ = ["RoomBookingAdmin", "RoomBookingResource"]
