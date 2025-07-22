"""Lab schedule aggregator URL patterns with router configuration."""

from rest_framework.routers import SimpleRouter

from ..views import LabScheduleViewSet

app_name = "lab_schedules"

router = SimpleRouter(trailing_slash=False)

router.register(r"lab-schedules", LabScheduleViewSet, basename="lab_schedule")

urlpatterns = router.urls
