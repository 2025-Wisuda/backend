"""
Guest Visit URLs for guest visit management.

Provides routes for:
- Guest visit CRUD operations
- Filtering and search capabilities
"""

from rest_framework.routers import SimpleRouter

from ..views import GuestVisitViewSet

app_name = "guest_visits"

router = SimpleRouter(trailing_slash=False)

router.register(r"guest-visits", GuestVisitViewSet, basename="guest_visits")

urlpatterns = router.urls
