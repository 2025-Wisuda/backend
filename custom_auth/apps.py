from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CustomAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "custom_auth"
    verbose_name = _("User Management")

    def ready(self):
        """
        Load application signals on startup.

        This ensures signal handlers like post_migrate are connected properly.
        Avoid direct database operations in this method to prevent
        issues during early app initialization or migrations.
        """
        from . import signals
