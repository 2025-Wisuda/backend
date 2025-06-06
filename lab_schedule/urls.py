"""
URL configuration for lab_schedule app.
"""

from django.urls import include, path

urlpatterns = [
    path("", include("lab_schedule.rest.urls.lab_schedule_urls")),
]
