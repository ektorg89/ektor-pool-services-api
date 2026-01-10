from pydantic import BaseModel, ConfigDict, field_validator, Field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    first_name: str
    last_name: str


class CustomerCreate(BaseModel):
    first_name: str
    last_name: str


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    invoice_id: int
    customer_id: int
    property_id: int

    period_start: date
    period_end: date

    status: str
    issued_date: date
    due_date: Optional[date]

    subtotal: Decimal
    tax: Decimal
    total: Decimal

    notes: Optional[str]

    created_at: datetime
    updated_at: datetime


class InvoiceCreate(BaseModel):
    customer_id: int = Field(..., ge=1, le=100, description="Customer ID (1-100)")
    property_id: int = Field(..., ge=1, le=100, description="Property ID (1-100)")

    period_start: date
    period_end: date

    status: str = "sent"
    issued_date: date
    due_date: Optional[date] = None

    subtotal: Decimal = Field(..., ge=0, le=10000, description="Subtotal (0-10000)")
    tax: Decimal = Field(..., ge=0, le=10000, description="Tax (0-10000)")
    total: Decimal = Field(..., ge=0, le=20000, description="Total (0-20000)")

    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"draft", "sent", "paid", "void"}
        if v not in allowed:
            raise ValueError("status must be one of: draft, sent, paid, void")
        return v

    @field_validator("period_end")
    @classmethod
    def validate_period_range(cls, v: date, info):
        start = info.data.get("period_start")
        if start is not None and start > v:
            raise ValueError("period_start cannot be after period_end")
        return v

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: Optional[date], info):
        issued = info.data.get("issued_date")
        if v is not None and issued is not None and issued > v:
            raise ValueError("issued_date cannot be after due_date")
        return v

    @field_validator("total")
    @classmethod
    def validate_total(cls, v: Decimal, info):
        data = info.data
        subtotal = data.get("subtotal")
        tax = data.get("tax")
        if subtotal is not None and tax is not None:
            if v != (subtotal + tax):
                raise ValueError("total must equal subtotal + tax")
        return v


class StatementItem(BaseModel):
    invoice_id: int
    issued_date: date
    status: str
    total: Decimal


class CustomerStatementOut(BaseModel):
    customer_id: int
    from_date: date
    to_date: date
    total: Decimal
    items: list[StatementItem]

class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None