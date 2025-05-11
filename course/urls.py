from django.urls import path
from course.views import CourseViewSet, CourseSessionViewSet

urlpatterns = [
    path(
        "courses",
        CourseViewSet.as_view({"get": "list", "post": "create"}),
        name="course-list",
    ),
    path(
        "courses/<uuid:pk>",
        CourseViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="course-detail",
    ),
    path(
        "courses/<uuid:pk>/enroll",
        CourseViewSet.as_view({"post": "enroll"}),
        name="course-enroll",
    ),
    path(
        "courses/sessions",
        CourseSessionViewSet.as_view({"get": "list", "post": "create"}),
        name="session-list",
    ),
    path(
        "courses/sessions/<uuid:pk>",
        CourseSessionViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="session-detail",
    ),
]
