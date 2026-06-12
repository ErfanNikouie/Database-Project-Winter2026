from django.contrib.auth import authenticate
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.api.serializers import (
    CurrentUserUpdateSerializer,
    LoginSerializer,
    LogoutSerializer,
    RefreshSerializer,
)
from apps.common.exceptions import ValidationException
from apps.forms.serializers.data_serializers import ErrorEnvelopeSerializer, GenericSuccessEnvelopeSerializer


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentication"],
        operation_id="auth_login",
        summary="Authenticate user and issue JWT tokens",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(response=GenericSuccessEnvelopeSerializer),
            401: OpenApiResponse(response=ErrorEnvelopeSerializer),
            422: OpenApiResponse(response=ErrorEnvelopeSerializer),
        },
        examples=[
            OpenApiExample(
                "Login Request",
                value={"username": "admin", "password": "password"},
                request_only=True,
            ),
            OpenApiExample(
                "Login Response",
                value={
                    "success": True,
                    "data": {
                        "access": "<jwt-access-token>",
                        "refresh": "<jwt-refresh-token>",
                        "user": {"id": 1, "username": "admin"},
                    },
                },
                response_only=True,
            ),
        ],
    )
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

    @extend_schema(
        tags=["Authentication"],
        operation_id="auth_refresh",
        summary="Refresh access token",
        request=RefreshSerializer,
        responses={200: OpenApiResponse(response=GenericSuccessEnvelopeSerializer), 401: OpenApiResponse(response=ErrorEnvelopeSerializer)},
        examples=[
            OpenApiExample("Refresh Request", value={"refresh": "<jwt-refresh-token>"}, request_only=True),
            OpenApiExample("Refresh Response", value={"success": True, "data": {"access": "<jwt-access-token>"}}, response_only=True),
        ],
    )
    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = RefreshToken(serializer.validated_data["refresh"])
        return Response({"success": True, "data": {"access": str(token.access_token)}})


class LogoutAPIView(APIView):
    @extend_schema(
        tags=["Authentication"],
        operation_id="auth_logout",
        summary="Blacklist refresh token and logout",
        request=LogoutSerializer,
        responses={200: OpenApiResponse(response=GenericSuccessEnvelopeSerializer), 401: OpenApiResponse(response=ErrorEnvelopeSerializer)},
        examples=[
            OpenApiExample("Logout Request", value={"refresh": "<jwt-refresh-token>"}, request_only=True),
            OpenApiExample("Logout Response", value={"success": True, "data": {"message": "Logged out"}}, response_only=True),
        ],
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = RefreshToken(serializer.validated_data["refresh"])
        token.blacklist()
        return Response({"success": True, "data": {"message": "Logged out"}}, status=status.HTTP_200_OK)


class CurrentUserAPIView(APIView):
    @extend_schema(
        tags=["Authentication"],
        operation_id="auth_current_user",
        summary="Get current authenticated user profile",
        responses={
            200: OpenApiResponse(response=GenericSuccessEnvelopeSerializer),
            401: OpenApiResponse(response=ErrorEnvelopeSerializer),
        },
    )
    def get(self, request):
        return Response({"success": True, "data": _serialize_user(request.user)})

    @extend_schema(
        tags=["Authentication"],
        operation_id="auth_update_current_user",
        summary="Update current authenticated user profile and password",
        request=CurrentUserUpdateSerializer,
        responses={
            200: OpenApiResponse(response=GenericSuccessEnvelopeSerializer),
            400: OpenApiResponse(response=ErrorEnvelopeSerializer),
            401: OpenApiResponse(response=ErrorEnvelopeSerializer),
            409: OpenApiResponse(response=ErrorEnvelopeSerializer),
        },
        examples=[
            OpenApiExample(
                "Update profile",
                value={"username": "admin"},
                request_only=True,
            ),
            OpenApiExample(
                "Change password",
                value={
                    "current_password": "OldSecret123!",
                    "new_password": "NewSecret123!",
                    "confirm_new_password": "NewSecret123!",
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = CurrentUserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        payload = serializer.validated_data

        username = payload.get("username")
        if username and username != user.username:
            if user.__class__.objects.filter(username=username).exclude(id=user.id).exists():
                raise ValidationException("Username already exists", field="username", status_code=409)
            user.username = username

        if payload.get("new_password"):
            if not user.check_password(payload["current_password"]):
                raise ValidationException("Current password is invalid", field="current_password")
            user.set_password(payload["new_password"])

        user.save()
        return Response({"success": True, "data": _serialize_user(user)})


def _serialize_user(user) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "groups": [
            {"id": group.id, "name": group.name}
            for group in user.groups_ref.all().order_by("name")
        ],
    }


