from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LabAllocationConfig(AppConfig):
    """Configuration for duty_schedule application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "duty_schedule"
    verbose_name = _("Duty Schedule")
