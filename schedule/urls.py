from django.urls import path
from .views import LabScheduleViewSet

urlpatterns = [
    path(
        "schedules/lab",
        LabScheduleViewSet.as_view({"get": "list", "post": "create"}),
        name="lab-schedules-list",
    ),
    path(
        "schedules/lab/<int:pk>",
        LabScheduleViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "destroy"}
        ),
        name="lab-schedule-detail",
    ),
]
