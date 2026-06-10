from django.urls import path

from apps.forms.api.views import (
    DataDeleteAPIView,
    DataDetailAPIView,
    DataInsertAPIView,
    DataListAPIView,
    DataUpdateAPIView,
)

urlpatterns = [
    path("insert", DataInsertAPIView.as_view(), name="data-insert"),
    path("update", DataUpdateAPIView.as_view(), name="data-update"),
    path("delete", DataDeleteAPIView.as_view(), name="data-delete"),
    path("detail", DataDetailAPIView.as_view(), name="data-detail"),
    path("list", DataListAPIView.as_view(), name="data-list"),
]

