class HRMSException(Exception):
    def __init__(self, message: str, status_code: int = 400, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.field = field


class ValidationException(HRMSException):
    pass


class PermissionDeniedException(HRMSException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=403)


class NotFoundException(HRMSException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)

