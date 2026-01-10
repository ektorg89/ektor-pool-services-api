from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Customer, Invoice, Property
from app.schemas.schemas import InvoiceCreate, InvoiceOut

router = APIRouter()


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    status: Optional[str] = Query(
        default=None,
        pattern="^(draft|sent|paid|void)$",
        description="Filter by invoice status: draft, sent, paid, void",
    ),
    customer_id: Optional[int] = Query(default=None, ge=1, le=100),
    property_id: Optional[int] = Query(default=None, ge=1, le=100),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(Invoice)

    if status is not None:
        q = q.filter(Invoice.status == status)

    if customer_id is not None:
        q = q.filter(Invoice.customer_id == customer_id)

    if property_id is not None:
        q = q.filter(Invoice.property_id == property_id)

    if from_date is not None:
        q = q.filter(Invoice.issued_date >= from_date)

    if to_date is not None:
        q = q.filter(Invoice.issued_date <= to_date)

    return q.order_by(Invoice.invoice_id.desc()).limit(50).all()
