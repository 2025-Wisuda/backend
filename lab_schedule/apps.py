"""Django app configuration for lab schedule module."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LabScheduleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lab_schedule"
    verbose_name = _("Lab Schedule Management")

    def ready(self):
        """Import admin configuration to set up grouped admin interface."""
        try:
            from .admins.admin_config import LabScheduleManagementAdminConfig

            # Configuration is applied during import
        except ImportError:
            pass
