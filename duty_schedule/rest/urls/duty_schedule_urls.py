"""
Duty Schedule URLs for DutyScheduleModel (Bulk Schedule Management).

Provides routes for:
- Duty schedule listing (read-only for public display)
"""

from rest_framework.routers import SimpleRouter

from ..views import DutyScheduleViewSet

app_name = "duty_schedules"

router = SimpleRouter(trailing_slash=False)

router.register(r"duty-schedules", DutyScheduleViewSet, basename="duty_schedule")

urlpatterns = router.urls
