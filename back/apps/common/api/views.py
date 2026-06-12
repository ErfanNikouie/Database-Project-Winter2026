from __future__ import annotations

import hashlib

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.forms.models import Form, FormField
from apps.forms.serializers.data_serializers import ErrorEnvelopeSerializer, GenericSuccessEnvelopeSerializer
from apps.lookups.models import Lookup, LookupValue
from apps.menus.models import Menu


class MetadataVersionAPIView(APIView):
    @extend_schema(
        tags=["System"],
        operation_id="metadata_version",
        summary="Return metadata checksum for frontend cache invalidation",
        responses={
            200: OpenApiResponse(response=GenericSuccessEnvelopeSerializer),
            401: OpenApiResponse(response=ErrorEnvelopeSerializer),
        },
        examples=[
            OpenApiExample(
                "Metadata version response",
                value={"success": True, "data": {"version": "b4cf41f2f4f4..."}},
                response_only=True,
            )
        ],
    )
    def get(self, request):
        digest = hashlib.sha256()
        self._update_digest(
            digest,
            Form.objects.order_by("id").values_list("id", "name", "table_name", "is_system", "updated_at"),
        )
        self._update_digest(
            digest,
            FormField.objects.order_by("id").values_list(
                "id",
                "form_id",
                "name",
                "type",
                "mandatory",
                "unique",
                "lookup_id",
                "foreign_key_table",
                "foreign_key_field",
                "sort_order",
                "is_system",
            ),
        )
        self._update_digest(
            digest,
            Menu.objects.order_by("id").values_list(
                "id",
                "name",
                "parent_menu_id",
                "form_id",
                "sort_order",
                "is_system",
            ),
        )
        self._update_digest(
            digest,
            Lookup.objects.order_by("id").values_list("id", "name", "description"),
        )
        self._update_digest(
            digest,
            LookupValue.objects.order_by("id").values_list("id", "lookup_id", "value"),
        )
        return Response({"success": True, "data": {"version": digest.hexdigest()}})

    @staticmethod
    def _update_digest(digest, rows) -> None:
        for row in rows:
            digest.update(str(tuple(row)).encode("utf-8"))


