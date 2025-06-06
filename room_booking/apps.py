from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RoomBookingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "room_booking"
    verbose_name = _("Room Booking Management")

    def ready(self):
        """
        Import signals when the app is ready
        """
        from . import signals
