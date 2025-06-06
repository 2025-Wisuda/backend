"""
Duty Attendance URLs for DutyAttendanceModel (Individual Attendance Tracking).

Provides routes for:
- Duty attendance listing and detail views
- Clock in/out operations with OTP validation
- Attendance history management
"""

from rest_framework.routers import SimpleRouter

from ..views import DutyAttendanceViewSet

app_name = "duty_attendances"

router = SimpleRouter(trailing_slash=False)

router.register(r"duty-attendances", DutyAttendanceViewSet, basename="duty_attendance")

urlpatterns = router.urls
