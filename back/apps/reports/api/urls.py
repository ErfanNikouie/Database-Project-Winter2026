from django.urls import path

from apps.reports.api.views import AvailableReportsAPIView, RunReportAPIView

urlpatterns = [
    path("available", AvailableReportsAPIView.as_view(), name="reports-available"),
    path("run", RunReportAPIView.as_view(), name="reports-run"),
]

