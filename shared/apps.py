"""
Django app configuration for the shared utilities.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SharedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shared"
    verbose_name = _("Shared Utilities")
