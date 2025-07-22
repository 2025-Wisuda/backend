"""
Custom Auth URLs

Root URL configuration for custom authentication module.
Organizes authentication and user management endpoints under logical namespaces.
"""

from django.urls import include, path

app_name = "custom_auth"

urlpatterns = [
    path("auth", include("custom_auth.rest.urls.auth_urls", namespace="auth")),
    path("", include("custom_auth.rest.urls.user_urls", namespace="users")),
]
