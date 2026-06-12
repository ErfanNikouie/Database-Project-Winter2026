from django.urls import path

from apps.menus.api.views import MenuTreeAPIView

urlpatterns = [
    path("tree", MenuTreeAPIView.as_view(), name="menu-tree"),
]

