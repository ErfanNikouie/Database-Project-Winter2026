from django.urls import path

from apps.authentication.api.views import (
    CurrentUserAPIView,
    LoginAPIView,
    LogoutAPIView,
    RefreshTokenAPIView,
)

urlpatterns = [
    path("login", LoginAPIView.as_view(), name="api-login"),
    path("refresh", RefreshTokenAPIView.as_view(), name="api-refresh"),
    path("logout", LogoutAPIView.as_view(), name="api-logout"),
    path("me", CurrentUserAPIView.as_view(), name="api-current-user"),
]

