from django.urls import path
from .views import LabScheduleViewSet, LabScheduleApprovalViewSet, DutyScheduleViewSet

urlpatterns = [
    path(
        "schedules/lab",
        LabScheduleViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="lab-schedules-list",
    ),
    path(
        "schedules/lab/<uuid:pk>",
        LabScheduleViewSet.as_view(
            {
                "get": "retrieve",
            }
        ),
        name="lab-schedule-detail",
    ),
    path(
        "schedules/lab/<uuid:pk>/approval",
        LabScheduleApprovalViewSet.as_view({"patch": "partial_update"}),
        name="lab-schedule-approval",
    ),
    path(
        "schedules/duty",
        DutyScheduleViewSet.as_view({"get": "list"}),
        name="duty-schedules-list",
    ),
    path(
        "schedules/duty/<uuid:pk>",
        DutyScheduleViewSet.as_view({"get": "retrieve"}),
        name="duty-schedule-detail",
    ),
    path(
        "schedules/lab/availability",
        LabScheduleViewSet.as_view({"get": "availability"}),
        name="lab-schedule-availability",
    ),
]
