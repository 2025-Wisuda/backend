"""
URL configuration for lab_schedule app.
"""

from django.urls import include, path

urlpatterns = [
    path("", include("room_booking.rest.urls.room_booking_urls")),
]
