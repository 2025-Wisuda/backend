"""
Dashboard model for Lab Schedule admin sidebar.

Creates a virtual model that appears in Django admin sidebar
for easy access to dashboard functionality.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class LabScheduleDashboardModel(models.Model):
    """
    Virtual model for dashboard functionality.

    This model doesn't store any data but provides a way to
    add dashboard link to Django admin sidebar.
    """

    class Meta:
        managed = False  # Django won't manage this table
        verbose_name = _("Lab Schedule Dashboard")
        verbose_name_plural = _("Dashboard")
        # Permission names that will be created
        permissions = [
            ("view_dashboard", "Can view lab schedule dashboard"),
        ]

    def __str__(self):
        return "Lab Schedule Dashboard"
