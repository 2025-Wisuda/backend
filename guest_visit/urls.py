# filepath: /Users/cg/Documents/MVP ONLY/guest_visit/urls.py
"""
URL configuration for guest_visit app.
"""

from django.urls import include, path

urlpatterns = [
    path("", include("guest_visit.rest.urls.guest_visit_urls")),
]