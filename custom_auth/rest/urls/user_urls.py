"""
User URLs for custom_auth app.

Single route for user listing, detail, and profile management.
"""

from rest_framework.routers import SimpleRouter

from ..views import UserViewSet

app_name = "users"

router = SimpleRouter(trailing_slash=False)

router.register(r"users", UserViewSet, basename="user")

urlpatterns = router.urls
