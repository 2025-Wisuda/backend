from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LabAllocationConfig(AppConfig):
    """Configuration for lab_allocation application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "lab_allocation"
    verbose_name = _("Lab Allocation")

    def ready(self):
        """
        Load application signals on startup.

        This ensures signal handlers for LabAllocation sync with LabSchedule
        aggregator are connected properly for conflict detection.
        Avoid direct database operations in this method to prevent
        issues during early app initialization or migrations.
        """
        from . import signals
