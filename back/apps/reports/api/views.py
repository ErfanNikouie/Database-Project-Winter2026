from __future__ import annotations

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.forms.serializers.data_serializers import ErrorEnvelopeSerializer, GenericSuccessEnvelopeSerializer
from apps.reports.api.serializers import RunReportSerializer
from apps.reports.report_service import DynamicReportService


class AvailableReportsAPIView(APIView):
    @extend_schema(
        tags=["Reports"],
        operation_id="reports_available",
        summary="List reports accessible to the current user",
        responses={
            200: OpenApiResponse(response=GenericSuccessEnvelopeSerializer),
            401: OpenApiResponse(response=ErrorEnvelopeSerializer),
            403: OpenApiResponse(response=ErrorEnvelopeSerializer),
        },
    )
    def get(self, request):
        items = DynamicReportService.list_available_reports(user=request.user)
        return Response({"success": True, "data": {"items": items}})


class RunReportAPIView(APIView):
    @extend_schema(
        tags=["Reports"],
        operation_id="reports_run",
        summary="Execute metadata-driven report",
        request=RunReportSerializer,
        responses={
            200: OpenApiResponse(response=GenericSuccessEnvelopeSerializer),
            400: OpenApiResponse(response=ErrorEnvelopeSerializer),
            401: OpenApiResponse(response=ErrorEnvelopeSerializer),
            403: OpenApiResponse(response=ErrorEnvelopeSerializer),
            404: OpenApiResponse(response=ErrorEnvelopeSerializer),
        },
        examples=[
            OpenApiExample(
                "Run report",
                value={
                    "report_id": 1,
                    "filters": {},
                    "sort_by": "username",
                    "sort_direction": "asc",
                    "limit": 100,
                    "offset": 0,
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = RunReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        result = DynamicReportService.run_report(
            user=request.user,
            report_id=payload["report_id"],
            filters=payload.get("filters") or {},
            sort_by=payload.get("sort_by") or None,
            sort_direction=payload["sort_direction"],
            limit=payload["limit"],
            offset=payload["offset"],
        )
        return Response({"success": True, "data": result})


class ReportDefinitionAPIView(APIView):
    @extend_schema(
        tags=["Reports"],
        operation_id="reports_definition",
        summary="Get visible report field definition for current user",
        responses={
            200: OpenApiResponse(response=GenericSuccessEnvelopeSerializer),
            400: OpenApiResponse(response=ErrorEnvelopeSerializer),
            401: OpenApiResponse(response=ErrorEnvelopeSerializer),
            403: OpenApiResponse(response=ErrorEnvelopeSerializer),
            404: OpenApiResponse(response=ErrorEnvelopeSerializer),
        },
    )
    def get(self, request, report_id: int):
        definition = DynamicReportService.get_report_definition(user=request.user, report_id=report_id)
        return Response({"success": True, "data": definition})


