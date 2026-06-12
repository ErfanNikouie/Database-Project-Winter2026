from django.urls import path

from apps.common.api.views import MetadataVersionAPIView

urlpatterns = [
    path("metadata/version", MetadataVersionAPIView.as_view(), name="metadata-version"),
]

