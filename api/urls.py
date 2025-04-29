from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/docs/", include("docs.urls")),
    path("api/v1/", include("custom_auth.urls")),
    path("api/v1/", include("schedule.urls")),
]
