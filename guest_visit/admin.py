"""
Guest visit admin configuration.
Manual admin registration.
"""

from django.contrib import admin

from .admins.guest_visit_admin import GuestVisitAdmin
from .models import GuestVisitModel

# Manual registration
admin.site.register(GuestVisitModel, GuestVisitAdmin)

__all__ = [
    "GuestVisitAdmin",
]
