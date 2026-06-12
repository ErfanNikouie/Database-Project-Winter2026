"""URL configuration for HRMS project."""
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.contrib import admin
from django.urls import include, path

from apps.common.api.schema_views import HRMSRedocView, HRMSSchemaView, HRMSSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.api.urls')),
    path('api/system/', include('apps.common.api.urls')),
    path('api/menus/', include('apps.menus.api.urls')),
    path('api/data/', include('apps.forms.api.urls')),
    path('api/forms/', include('apps.forms.api.form_urls')),
]

if settings.ENABLE_SWAGGER:
    schema_view = cache_page(settings.SWAGGER_SCHEMA_CACHE_TIMEOUT)(HRMSSchemaView.as_view())
    urlpatterns += [
        path('api/schema/', schema_view, name='api-schema'),
        path('api/docs/', HRMSSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
        path('api/redoc/', HRMSRedocView.as_view(url_name='api-schema'), name='api-redoc'),
    ]
