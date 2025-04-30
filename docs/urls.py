from django.urls import path
from .views import SchemaView, SwaggerView, RedocView

urlpatterns = [
    path('schema', SchemaView.as_view(), name='schema'),
    path('swagger', SwaggerView.as_view(), name='swagger-ui'),
    path('redoc', RedocView.as_view(), name='redoc'),
]
