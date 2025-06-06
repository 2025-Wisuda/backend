"""
Main URLs for custom_auth app.

Includes both authentication and user management endpoints.
"""

from django.urls import include, path

app_name = "custom_auth"

urlpatterns = [
    path("auth", include("custom_auth.rest.urls.auth_urls", namespace="auth")),
    path("", include("custom_auth.rest.urls.user_urls", namespace="users")),
]
