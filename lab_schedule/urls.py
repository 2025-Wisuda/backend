"""
Main URLs for lab_schedule app.

Includes laboratory schedule aggregator and conflict detection endpoints.
"""

from django.urls import include, path

urlpatterns = [
    path("", include("lab_schedule.rest.urls.lab_schedule_urls")),
]
