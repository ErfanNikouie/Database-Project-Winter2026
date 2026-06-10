from django.urls import path

from apps.authentication.api.views import LoginAPIView, LogoutAPIView, RefreshTokenAPIView

urlpatterns = [
    path("login", LoginAPIView.as_view(), name="api-login"),
    path("refresh", RefreshTokenAPIView.as_view(), name="api-refresh"),
    path("logout", LogoutAPIView.as_view(), name="api-logout"),
]

