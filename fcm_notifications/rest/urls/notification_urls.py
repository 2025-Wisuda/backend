from rest_framework.routers import SimpleRouter

from ..views.notification_views import NotificationLogViewSet

app_name = "fcm_notifications"

router = SimpleRouter(trailing_slash=False)
router.register(r"notifications", NotificationLogViewSet, basename="notifications")

urlpatterns = router.urls
