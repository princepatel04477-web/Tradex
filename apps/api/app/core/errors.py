"""Domain exception hierarchy mapping cleanly to HTTP status codes and error codes."""

from typing import Any, Optional


class TradlyException(Exception):
    """Base exception for all Tradly domain errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class ValidationError(TradlyException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422, details=details)


class ResourceNotFoundError(TradlyException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, code="NOT_FOUND", status_code=404, details=details)


class AuthenticationError(TradlyException):
    def __init__(self, message: str = "Invalid credentials or session expired"):
        super().__init__(message=message, code="UNAUTHENTICATED", status_code=401)


class AuthorizationError(TradlyException):
    def __init__(self, message: str = "Access denied by security policy"):
        super().__init__(message=message, code="FORBIDDEN", status_code=403)


ForbiddenError = AuthorizationError


class InsufficientMarginError(TradlyException):
    def __init__(self, required: str, available: str):
        message = f"Insufficient Free Margin: order requires ${required}, but only ${available} is available."
        super().__init__(message=message, code="INSUFFICIENT_MARGIN", status_code=400, details={"required": required, "available": available})


class RateLimitExceededError(TradlyException):
    def __init__(self, message: str = "Rate limit exceeded. Please retry later."):
        super().__init__(message=message, code="RATE_LIMIT_EXCEEDED", status_code=429)


class ProviderUnavailableError(TradlyException):
    def __init__(self, provider_name: str, message: str = "Provider temporarily unavailable"):
        super().__init__(message=f"{provider_name}: {message}", code="PROVIDER_UNAVAILABLE", status_code=503)


class ConflictError(TradlyException):
    def __init__(self, message: str):
        super().__init__(message=message, code="RESOURCE_CONFLICT", status_code=409)
