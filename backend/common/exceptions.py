import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, Throttled, ValidationError

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """
    Raised by service layer functions for expected business rule violations.
    These are translated to 400 responses - they are not bugs.
    """

    def __init__(self, message: str, code: str = "service_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(ServiceError):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found."):
        super().__init__(message, code="not_found")


class PermissionError(ServiceError):
    """Raised when a user lacks permission for an operation."""

    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(message, code="permission_denied")


class ConflictError(ServiceError):
    """Raised when an operation conflicts with existing data."""

    def __init__(self, message: str):
        super().__init__(message, code="conflict")


def custom_exception_handler(exc, context):
    """
    Extends DRF's default handler.
    ServiceError subclasses become structured 400/403/404 responses.
    Unhandled exceptions are logged and return 500.
    """

    if isinstance(exc, ServiceError):
        if isinstance(exc, NotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, PermissionError):
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, ConflictError):
            status_code = status.HTTP_409_CONFLICT
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        return Response(
            {"detail": exc.message, "code": exc.code},
            status=status_code,
        )

    response = exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled exception in view %s", context.get("view"))
        return Response(
            {"detail": "An unexpected error occurred. Our team has been notified."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, Throttled):
        response.data = {
            "detail": "Request was throttled. Please try again later.",
            "code": "rate_limited",
            "wait": getattr(exc, "wait", None),
        }
    elif isinstance(exc, ValidationError):
        field_errors = response.data
        response.data = {
            "detail": "Validation failed.",
            "code": "validation_error",
            "fields": field_errors,
        }
        if isinstance(field_errors, dict):
            response.data.update(field_errors)
    elif isinstance(exc, PermissionDenied):
        response.data = {
            "detail": str(response.data.get("detail", "Permission denied.")) if isinstance(response.data, dict) else "Permission denied.",
            "code": "permission_denied",
        }
    elif isinstance(exc, NotFound):
        response.data = {
            "detail": str(response.data.get("detail", "Not found.")) if isinstance(response.data, dict) else "Not found.",
            "code": "not_found",
        }

    return response
