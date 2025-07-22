from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GuestVisitConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "guest_visit"
    verbose_name = _("Guest Visit")
