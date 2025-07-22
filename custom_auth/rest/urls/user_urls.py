"""
User URLs

URL routing for user management endpoints using DRF ViewSet routing.
Provides RESTful endpoints for user CRUD operations and profile management.
"""

from rest_framework.routers import SimpleRouter

from ..views import UserViewSet

app_name = "users"

router = SimpleRouter(trailing_slash=False)

router.register(r"users", UserViewSet, basename="user")

urlpatterns = router.urls
