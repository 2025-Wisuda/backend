"""
URL patterns for Face Recognition API.

Provides URL routing for face recognition endpoints
that can be used across different modules.
"""

from django.urls import path

from .views.face_recognition_views import (
    get_face_recognition_stats,
    get_users_without_face_data,
    identify_user_from_face,
    process_face_recognition,
    register_user_face,
    verify_user_face,
)

app_name = "face_recognition"

urlpatterns = [
    # Face recognition processing
    path("process/", process_face_recognition, name="process"),
    # User identification
    path("identify/", identify_user_from_face, name="identify"),
    # Face registration
    path("register/", register_user_face, name="register"),
    # Face verification
    path("verify/", verify_user_face, name="verify"),
    # Statistics and management
    path("stats/", get_face_recognition_stats, name="stats"),
    path(
        "users-without-face-data/",
        get_users_without_face_data,
        name="users-without-face-data",
    ),
]
