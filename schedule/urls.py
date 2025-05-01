from django.urls import path
from .views import LabScheduleViewSet, LabScheduleApprovalViewSet

urlpatterns = [
    path(
        "schedules/lab",
        LabScheduleViewSet.as_view({"get": "list", "post": "create"}),
        name="lab-schedules-list",
    ),
    path(
        "schedules/lab/<uuid:pk>",
        LabScheduleViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="lab-schedule-detail",
    ),
    path(
        "schedules/lab/<uuid:pk>/approval",
        LabScheduleApprovalViewSet.as_view({"put": "update"}),
        name="lab-schedule-approval",
    ),
]
