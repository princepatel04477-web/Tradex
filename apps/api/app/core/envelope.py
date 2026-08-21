"""REST response envelope format per SRS CI-4: { data, error, meta }."""

from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

from app.core.logging import get_correlation_id

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str = Field(description="Domain or HTTP error code string")
    message: str = Field(description="Plain language explanation of what went wrong")
    details: Optional[Any] = Field(default=None, description="Detailed validation error list or context")


class ResponseMeta(BaseModel):
    request_id: str = Field(default_factory=get_correlation_id, description="Correlation ID")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = "v1"


class ApiResponse(BaseModel, Generic[T]):
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)

    @classmethod
    def success(cls, data: T, meta: Optional[ResponseMeta] = None) -> "ApiResponse[T]":
        return cls(
            data=data,
            error=None,
            meta=meta or ResponseMeta(request_id=get_correlation_id()),
        )

    @classmethod
    def fail(cls, code: str, message: str, details: Optional[Any] = None) -> "ApiResponse[None]":
        return cls(
            data=None,
            error=ErrorDetail(code=code, message=message, details=details),
            meta=ResponseMeta(request_id=get_correlation_id()),
        )
