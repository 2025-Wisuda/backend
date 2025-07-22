"""
URL configuration for course app.

This module provides URL routing for the course application,
including REST API endpoints and any additional views.
"""

from django.urls import include, path

app_name = "course"

urlpatterns = [
    path("", include("course.rest.urls")),
]
