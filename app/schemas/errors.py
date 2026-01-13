from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str = Field(..., examples=["CUSTOMER_NOT_FOUND"])
    message: str = Field(..., examples=["customer not found"])
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationErrorItem(BaseModel):
    loc: list[Any]
    msg: str
    type: str


class RequestValidationErrorResponse(BaseModel):
    code: str = Field(default="REQUEST_VALIDATION_ERROR")
    message: str = Field(default="Invalid request")
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
