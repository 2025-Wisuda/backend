"""
Lab Schedule URLs for lab_schedule Aggregator.

Provides routes for:
- Lab schedule listing and detail views
- Lab availability checking
"""

from rest_framework.routers import SimpleRouter

from ..views import LabScheduleViewSet

app_name = "lab_schedules"

router = SimpleRouter(trailing_slash=False)

router.register(r"lab-schedules", LabScheduleViewSet, basename="lab_schedule")

urlpatterns = router.urls
