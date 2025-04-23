from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.permissions import AllowAny

class SchemaView(SpectacularAPIView):
    pass 

class SwaggerView(SpectacularSwaggerView):
    permission_classes = [AllowAny]
    
class RedocView(SpectacularRedocView):
    permission_classes = [AllowAny]