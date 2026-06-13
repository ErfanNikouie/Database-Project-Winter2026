from django.urls import path

from apps.reports.api.views import AvailableReportsAPIView, ReportDefinitionAPIView, RunReportAPIView

urlpatterns = [
    path("available", AvailableReportsAPIView.as_view(), name="reports-available"),
    path("definition/<int:report_id>", ReportDefinitionAPIView.as_view(), name="reports-definition"),
    path("run", RunReportAPIView.as_view(), name="reports-run"),
]

