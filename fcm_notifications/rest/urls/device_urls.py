from rest_framework.routers import SimpleRouter

from ..views.device_views import DeviceViewSet

app_name = "devices"

router = SimpleRouter(trailing_slash=False)
router.register(r"devices", DeviceViewSet, basename="devices")

urlpatterns = router.urls
