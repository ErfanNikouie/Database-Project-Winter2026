from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny, IsAuthenticated


class HRMSSchemaView(SpectacularAPIView):
    permission_classes = [IsAuthenticated] if settings.SWAGGER_REQUIRE_AUTH else [AllowAny]


class HRMSSwaggerView(SpectacularSwaggerView):
    permission_classes = [IsAuthenticated] if settings.SWAGGER_REQUIRE_AUTH else [AllowAny]


class HRMSRedocView(SpectacularRedocView):
    permission_classes = [IsAuthenticated] if settings.SWAGGER_REQUIRE_AUTH else [AllowAny]

