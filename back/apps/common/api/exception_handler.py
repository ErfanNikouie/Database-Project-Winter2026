from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.common.exceptions import HRMSException


def custom_exception_handler(exc, context):
    if isinstance(exc, HRMSException):
        payload = {"success": False, "error": {"message": exc.message}}
        if exc.field:
            payload["error"]["field"] = exc.field
        return Response(payload, status=exc.status_code)

    response = exception_handler(exc, context)
    if response is None:
        return Response(
            {"success": False, "error": {"message": f"Internal server error: {exc}"}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return Response({"success": False, "error": response.data}, status=response.status_code)

