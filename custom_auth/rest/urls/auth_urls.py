"""
Authentication URLs

URL routing for authentication endpoints including JWT token management.
Integrates with Django REST Framework SimpleJWT for token-based authentication.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from ..views import AuthViewSet

app_name = "auth"

urlpatterns = [
    path("/login", TokenObtainPairView.as_view(), name="login"),
    path("/refresh-token", TokenRefreshView.as_view(), name="refresh"),
    path(
        "/change-password",
        AuthViewSet.as_view({"post": "change_password"}),
        name="change_password",
    ),
    path("/logout", AuthViewSet.as_view({"post": "logout"}), name="logout"),
]
