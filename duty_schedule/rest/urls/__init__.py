"""
Main URL configuration for duty_schedule REST API.

Includes all REST API endpoints for duty schedules and attendance.
"""

from django.urls import include, path

urlpatterns = [
    # Duty Schedule endpoints (read-only)
    path("", include("duty_schedule.rest.urls.duty_schedule_urls")),
    # Duty Attendance endpoints (full CRUD + actions)
    path("", include("duty_schedule.rest.urls.duty_attendance_urls")),
]
