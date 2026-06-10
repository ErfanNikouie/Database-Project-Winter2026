from rest_framework.response import Response
from rest_framework.views import APIView

from apps.forms.serializers.data_serializers import (
    DeleteSerializer,
    DetailSerializer,
    InsertSerializer,
    ListSerializer,
    UpdateSerializer,
)
from apps.forms.services.crud_service import CrudService


class DataInsertAPIView(APIView):
    def post(self, request):
        serializer = InsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = CrudService.insert(user=request.user, **serializer.validated_data)
        return Response({"success": True, "data": row})


class DataUpdateAPIView(APIView):
    def post(self, request):
        serializer = UpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = CrudService.update(user=request.user, **serializer.validated_data)
        return Response({"success": True, "data": row})


class DataDeleteAPIView(APIView):
    def post(self, request):
        serializer = DeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        CrudService.delete(user=request.user, **serializer.validated_data)
        return Response({"success": True, "data": {"message": "Record deleted"}})


class DataDetailAPIView(APIView):
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
    def post(self, request):
        serializer = ListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = CrudService.list(user=request.user, **serializer.validated_data)
        return Response({"success": True, "data": {"count": result.count, "items": result.items}})

