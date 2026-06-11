from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.forms.serializers.data_serializers import (
    DeleteSerializer,
    DetailSerializer,
    InsertSerializer,
    ListSerializer,
    UpdateSerializer,
)
from apps.forms.services.crud_service import CrudService


# This serializer is for documentation purposes only
class _DataRequestSerializer(serializers.Serializer):
    form_name = serializers.CharField()
    data = serializers.DictField()


class DataInsertAPIView(APIView):
    @swagger_auto_schema(
        request_body=_DataRequestSerializer,
        responses={201: openapi.Response('Created', schema=openapi.Schema(type=openapi.TYPE_OBJECT))}
    )
    def post(self, request):
        serializer = InsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = CrudService.insert(user=request.user, **serializer.validated_data)
        return Response({"success": True, "data": row})


class DataUpdateAPIView(APIView):
    @swagger_auto_schema(request_body=_DataRequestSerializer)
    def post(self, request):
        serializer = UpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = CrudService.update(user=request.user, **serializer.validated_data)
        return Response({"success": True, "data": row})


class DataDeleteAPIView(APIView):
    @swagger_auto_schema(request_body=_DataRequestSerializer)
    def post(self, request):
        serializer = DeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        CrudService.delete(user=request.user, **serializer.validated_data)
        return Response({"success": True, "data": {"message": "Record deleted"}})


class DataDetailAPIView(APIView):
    @swagger_auto_schema(request_body=_DataRequestSerializer)
    def post(self, request):
        serializer = DetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = CrudService.detail(
            user=request.user,
            table_name=serializer.validated_data["table"],
            record_id=serializer.validated_data["id"],
        )
        return Response({"success": True, "data": row})


class DataListAPIView(APIView):
    @swagger_auto_schema(request_body=_DataRequestSerializer)
    def post(self, request):
        serializer = ListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = CrudService.list(user=request.user, **serializer.validated_data)
        return Response({"success": True, "data": {"count": result.count, "items": result.items}})

