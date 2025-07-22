from api import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Admin OTP Panel (before Django admin to avoid conflicts)
    path(
        "otp-admin/",
        TemplateView.as_view(template_name="admin_otp_panel.html"),
        name="admin_otp_panel",
    ),
    path("admin/", admin.site.urls),
    path("api/v1/schema", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/v1/", include("custom_auth.urls")),
    path("api/v1/", include("lab_schedule.urls")),
    path("api/v1/", include("room_booking.urls")),
    path("api/v1/", include("duty_schedule.urls")),
    path("api/v1/", include("course.urls")),
    path("api/v1/", include("guest_visit.urls")),
    path("api/v1/fcm/", include("fcm_notifications.urls")),
    # Removed i18n_urls to hide test-translations and language-info from Swagger
    # path("api/v1/", include("shared.rest.urls.i18n_urls")),
    path("api/v1/shared/", include("shared.rest.urls.shared_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
