"""BidAgent exception hierarchy.

All business exceptions inherit from BidAgentException.
The global exception handler converts them to uniform JSON responses.
"""


class BidAgentException(Exception):
    """Base exception for all BidAgent errors."""

    code: str = "INTERNAL_ERROR"
    status_code: int = 500
    message: str = "Internal server error"

    def __init__(self, message: str | None = None, **kwargs: object) -> None:
        if message:
            self.message = message
        self.detail = kwargs
        super().__init__(self.message)


class NotFoundError(BidAgentException):
    """Resource not found (404)."""

    code = "NOT_FOUND"
    status_code = 404

    def __init__(self, resource_type: str, resource_id: str) -> None:
        super().__init__(f"{resource_type} {resource_id} not found")


class ValidationError(BidAgentException):
    """Request validation error (422)."""

    code = "VALIDATION_ERROR"
    status_code = 422


class AuthenticationError(BidAgentException):
    """Authentication failed (401)."""

    code = "AUTHENTICATION_FAILED"
    status_code = 401

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)


class AuthorizationError(BidAgentException):
    """Forbidden — insufficient permissions (403)."""

    code = "FORBIDDEN"
    status_code = 403

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message)


class InsufficientCreditsError(BidAgentException):
    """Not enough credits to perform operation (402)."""

    code = "INSUFFICIENT_CREDITS"
    status_code = 402

    def __init__(self, required: int, available: int) -> None:
        super().__init__(
            f"Insufficient credits: need {required}, have {available}"
        )
        self.required = required
        self.available = available


class LLMError(BidAgentException):
    """LLM service call failed (502)."""

    code = "LLM_ERROR"
    status_code = 502


class CrawlerError(BidAgentException):
    """Crawler operation failed (502)."""

    code = "CRAWLER_ERROR"
    status_code = 502


class ExternalServiceError(BidAgentException):
    """External service unavailable (502)."""

    code = "EXTERNAL_SERVICE_ERROR"
    status_code = 502
