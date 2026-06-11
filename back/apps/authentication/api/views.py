from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema

from apps.authentication.api.serializers import LoginSerializer, LogoutSerializer, RefreshSerializer
from apps.common.exceptions import ValidationException


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request=request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if not user:
            raise ValidationException("Invalid credentials", status_code=401)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "success": True,
                "data": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": {"id": user.id, "username": user.username},
                },
            }
        )


class RefreshTokenAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = RefreshToken(serializer.validated_data["refresh"])
        return Response({"success": True, "data": {"access": str(token.access_token)}})


class LogoutAPIView(APIView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = RefreshToken(serializer.validated_data["refresh"])
        token.blacklist()
        return Response({"success": True, "data": {"message": "Logged out"}}, status=status.HTTP_200_OK)

