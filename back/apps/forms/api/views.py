from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.forms.models import Form
from apps.menus.models import Menu
from apps.common.exceptions import ValidationException
from apps.forms.serializers.data_serializers import (
    DeleteSerializer,
    DetailSerializer,
    ErrorEnvelopeSerializer,
    FormSchemaResponseSerializer,
    GenericListSuccessEnvelopeSerializer,
    GenericSuccessEnvelopeSerializer,
    InsertSerializer,
    ListSerializer,
    UpdateSerializer,
)
from apps.forms.services.crud_service import CrudService


class DataInsertAPIView(APIView):
    @extend_schema(
        tags=["Dynamic Data"],
        operation_id="data_insert",
        summary="Insert a record into any system or dynamic table",
        request=InsertSerializer,
        responses={
            200: OpenApiResponse(response=GenericSuccessEnvelopeSerializer),
            400: OpenApiResponse(response=ErrorEnvelopeSerializer),
            401: OpenApiResponse(response=ErrorEnvelopeSerializer),
            403: OpenApiResponse(response=ErrorEnvelopeSerializer),
            404: OpenApiResponse(response=ErrorEnvelopeSerializer),
            409: OpenApiResponse(response=ErrorEnvelopeSerializer),
            422: OpenApiResponse(response=ErrorEnvelopeSerializer),
            500: OpenApiResponse(response=ErrorEnvelopeSerializer),
        },
        examples=[
            OpenApiExample(
                "Insert Employee",
                value={"form": "Employee", "data": {"first_name": "John", "last_name": "Doe"}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert Contract",
                value={"form": "Contract", "data": {"employee_id": 12, "start_date": "2026-01-01", "salary": 2500}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert Training",
                value={"form": "Training", "data": {"title": "Leadership 101", "hours": 16}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert Project",
                value={"form": "Project", "data": {"name": "HRMS Rollout", "budget": 45000}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert Asset",
                value={"form": "Asset", "data": {"asset_code": "LT-1001", "assigned_to": 12}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert MedicalRecord",
                value={"form": "MedicalRecord", "data": {"employee_id": 12, "record_date": "2026-06-01", "status": "Healthy"}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert PerformanceEvaluation",
                value={"form": "PerformanceEvaluation", "data": {"employee_id": 12, "score": 92, "period": "2026-Q2"}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert Form Metadata",
                value={"menu": "Forms", "data": {"name": "Employee", "table_name": "employee", "is_system": False}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert Form Field Metadata",
                value={"menu": "Fields", "data": {"form_id": 10, "name": "first_name", "type": "String", "mandatory": True}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert ForeignKey Field Metadata",
                value={"menu": "Fields", "data": {"form_id": 12, "name": "department_id", "type": "ForeignKey", "mandatory": False, "unique": False, "foreign_key_form": "Department", "is_system": False}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert Menu Metadata",
                value={"menu": "Menus", "data": {"name": "Employees", "form_id": 10, "sort_order": 1}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert Permission Metadata",
                value={"menu": "Group Permissions", "data": {"menu_id": 20, "group_id": 2, "can_view": True, "can_insert": True, "can_update": True, "can_delete": False, "can_print": True}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert Lookup Metadata",
                value={"menu": "Lookups", "data": {"name": "ContractType", "description": "Contract type list"}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert Lookup Value Metadata",
                value={"menu": "Lookup Values", "data": {"lookup_id": 4, "value": "Permanent"}},
                request_only=True,
            ),
            OpenApiExample(
                "Insert Success",
                value={"success": True, "data": {"id": 1, "first_name": "John", "last_name": "Doe"}},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = InsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_table = _resolve_target_table(serializer.validated_data)
        row = CrudService.insert(user=request.user, table_name=target_table, data=serializer.validated_data["data"])
        return Response({"success": True, "data": row})


class DataUpdateAPIView(APIView):
    @extend_schema(
        tags=["Dynamic Data"],
        operation_id="data_update",
        summary="Update a record in any system or dynamic table",
        request=UpdateSerializer,
        responses={200: GenericSuccessEnvelopeSerializer, 400: ErrorEnvelopeSerializer, 401: ErrorEnvelopeSerializer, 403: ErrorEnvelopeSerializer, 404: ErrorEnvelopeSerializer, 409: ErrorEnvelopeSerializer, 422: ErrorEnvelopeSerializer, 500: ErrorEnvelopeSerializer},
        examples=[
            OpenApiExample("Update Employee", value={"form": "Employee", "data": {"id": 1, "first_name": "Updated"}}, request_only=True),
            OpenApiExample("Update Form Metadata", value={"menu": "Forms", "data": {"id": 9, "description": "Updated description"}}, request_only=True),
            OpenApiExample("Update Permission Metadata", value={"menu": "Group Permissions", "data": {"id": 5, "can_delete": False}}, request_only=True),
            OpenApiExample("Update Lookup Metadata", value={"menu": "Lookups", "data": {"id": 4, "description": "Updated lookup"}}, request_only=True),
        ],
    )
    def post(self, request):
        serializer = UpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_table = _resolve_target_table(serializer.validated_data)
        row = CrudService.update(user=request.user, table_name=target_table, data=serializer.validated_data["data"])
        return Response({"success": True, "data": row})


class DataDeleteAPIView(APIView):
    @extend_schema(
        tags=["Dynamic Data"],
        operation_id="data_delete",
        summary="Delete a record from any system or dynamic table",
        request=DeleteSerializer,
        responses={200: GenericSuccessEnvelopeSerializer, 400: ErrorEnvelopeSerializer, 401: ErrorEnvelopeSerializer, 403: ErrorEnvelopeSerializer, 404: ErrorEnvelopeSerializer, 409: ErrorEnvelopeSerializer, 422: ErrorEnvelopeSerializer, 500: ErrorEnvelopeSerializer},
        examples=[
            OpenApiExample("Delete Employee", value={"form": "Employee", "data": {"id": 1}}, request_only=True),
            OpenApiExample("Delete Lookup Value", value={"menu": "Lookup Values", "data": {"id": 12}}, request_only=True),
            OpenApiExample("Delete Form Field Metadata", value={"menu": "Fields", "data": {"id": 75}}, request_only=True),
        ],
    )
    def post(self, request):
        serializer = DeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_table = _resolve_target_table(serializer.validated_data)
        CrudService.delete(user=request.user, table_name=target_table, data=serializer.validated_data["data"])
        return Response({"success": True, "data": {"message": "Record deleted"}})


class DataDetailAPIView(APIView):
    @extend_schema(
        tags=["Dynamic Data"],
        operation_id="data_detail",
        summary="Retrieve one record by id from any system or dynamic table",
        request=DetailSerializer,
        responses={200: GenericSuccessEnvelopeSerializer, 400: ErrorEnvelopeSerializer, 401: ErrorEnvelopeSerializer, 403: ErrorEnvelopeSerializer, 404: ErrorEnvelopeSerializer, 422: ErrorEnvelopeSerializer, 500: ErrorEnvelopeSerializer},
        examples=[
            OpenApiExample("Detail Employee", value={"form": "Employee", "id": 15}, request_only=True),
            OpenApiExample("Detail Response", value={"success": True, "data": {"id": 15, "first_name": "John"}}, response_only=True),
        ],
    )
    def post(self, request):
        serializer = DetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_table = _resolve_target_table(serializer.validated_data)
        row = CrudService.detail(
            user=request.user,
            table_name=target_table,
            record_id=serializer.validated_data["id"],
        )
        return Response({"success": True, "data": row})


class DataListAPIView(APIView):
    @extend_schema(
        tags=["Dynamic Data"],
        operation_id="data_list",
        summary="List records from any system or dynamic table with filtering and paging",
        request=ListSerializer,
        responses={200: GenericListSuccessEnvelopeSerializer, 400: ErrorEnvelopeSerializer, 401: ErrorEnvelopeSerializer, 403: ErrorEnvelopeSerializer, 404: ErrorEnvelopeSerializer, 422: ErrorEnvelopeSerializer, 500: ErrorEnvelopeSerializer},
        examples=[
            OpenApiExample(
                "List Employee",
                value={
                    "form": "Employee",
                    "limit": 50,
                    "offset": 0,
                    "sort_by": "id",
                    "sort_direction": "asc",
                    "filters": {"salary": ">1000", "name": "John|Ali"},
                },
                request_only=True,
            ),
            OpenApiExample(
                "List Menus (Metadata)",
                value={"menu": "Menus", "limit": 50, "offset": 0, "sort_by": "id", "sort_direction": "asc", "filters": {}},
                request_only=True,
            ),
            OpenApiExample(
                "List Permissions (Metadata)",
                value={"menu": "Group Permissions", "limit": 50, "offset": 0, "sort_by": "id", "sort_direction": "asc", "filters": {"group_id": 2}},
                request_only=True,
            ),
            OpenApiExample(
                "List Forms (Metadata)",
                value={"menu": "Forms", "limit": 50, "offset": 0, "sort_by": "id", "sort_direction": "asc", "filters": {"is_system": False}},
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = ListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_table = _resolve_target_table(serializer.validated_data)
        result = CrudService.list(
            user=request.user,
            table_name=target_table,
            limit=serializer.validated_data["limit"],
            offset=serializer.validated_data["offset"],
            sort_by=serializer.validated_data["sort_by"],
            sort_direction=serializer.validated_data["sort_direction"],
            filters=serializer.validated_data.get("filters") or {},
        )
        return Response({"success": True, "data": {"count": result.count, "items": result.items}})


class FormSchemaAPIView(APIView):
    @extend_schema(
        tags=["Forms"],
        operation_id="form_runtime_schema",
        summary="Get runtime schema for a form",
        parameters=[
            OpenApiParameter(
                name="form_name",
                required=True,
                type=OpenApiTypes.STR,
                location="path",
                description="Form table name, for example 'employee'.",
            )
        ],
        responses={
            200: OpenApiResponse(response=FormSchemaResponseSerializer),
            404: OpenApiResponse(response=ErrorEnvelopeSerializer),
            401: OpenApiResponse(response=ErrorEnvelopeSerializer),
            403: OpenApiResponse(response=ErrorEnvelopeSerializer),
        },
        examples=[
            OpenApiExample(
                "Form Schema Response",
                value={
                    "form": "employee",
                    "table": "employee",
                    "fields": [
                        {"name": "first_name", "type": "String", "required": True, "unique": False},
                        {"name": "last_name", "type": "String", "required": True, "unique": False},
                    ],
                },
                response_only=True,
            )
        ],
    )
    def get(self, request, form_name: str):
        form = get_object_or_404(Form.objects.prefetch_related("fields"), table_name=form_name)
        fields = []
        for field in form.fields.all().order_by("sort_order", "id"):
            fields.append(
                {
                    "name": field.name,
                    "type": field.type,
                    "required": field.mandatory,
                    "unique": field.unique,
                    "lookup_id": field.lookup_id,
                    "foreign_key_table": field.foreign_key_table,
                    "foreign_key_field": field.foreign_key_field,
                }
            )

        return Response({"form": form.name, "table": form.table_name, "fields": fields})


def _resolve_target_table(payload: dict) -> str:
    form_name = payload.get("form")
    menu_name = payload.get("menu")

    if form_name:
        form = Form.objects.filter(name=form_name).order_by("id").first()
        if not form:
            raise ValidationException("Unknown form", field="form")
        return form.table_name

    menu_qs = Menu.objects.filter(name=menu_name)
    if menu_qs.count() > 1:
        raise ValidationException("Menu name is ambiguous. Use a unique menu name.", field="menu")
    menu = menu_qs.first()
    if not menu:
        raise ValidationException("Unknown menu", field="menu")
    if not menu.form_id:
        raise ValidationException("Menu is a folder and is not bound to a form.", field="menu")
    return menu.form.table_name


