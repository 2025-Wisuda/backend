"""Course module configuration with signal and admin initialization."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CourseConfig(AppConfig):
    """Course application configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "course"
    verbose_name = _("Course Management")

    def ready(self):
        """Initialize signals and admin interfaces on app startup."""
        import course.admins  # noqa: F401
        import course.signals  # noqa: F401
