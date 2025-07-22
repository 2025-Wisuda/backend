"""
Custom Auth App Configuration

Django app configuration for custom authentication module.
Handles app initialization, signal registration, and metadata.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CustomAuthConfig(AppConfig):
    """
    Configuration for custom authentication app.

    Features:
    - Internationalization support
    - Signal registration for automatic group/permission creation
    - UUID field configuration
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "custom_auth"
    verbose_name = _("User Management")

    def ready(self):
        """Import signals to auto-create groups and permissions after migrations."""
        from . import signals
