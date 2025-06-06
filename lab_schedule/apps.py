from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LabScheduleConfig(AppConfig):
    """Configuration for lab_schedule application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "lab_schedule"
    verbose_name = _("Lab Schedule Management")
