from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Customer, Invoice, Property
from app.schemas.schemas import InvoiceCreate, InvoiceOut

router = APIRouter()


@router.get(
    "",
    response_model=list[InvoiceOut],
    operation_id="v1_invoices_list",
)
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


@router.get(
    "/{invoice_id}",
    response_model=InvoiceOut,
    operation_id="v1_invoices_get",
)
def get_invoice(
    invoice_id: int = Path(..., ge=1, description="Invoice ID (>= 1)"),
    db: Session = Depends(get_db),
):
    row = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return row


@router.post(
    "",
    response_model=InvoiceOut,
    status_code=201,
    operation_id="v1_invoices_create",
)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    customer_exists = (
        db.query(Customer.customer_id)
        .filter(Customer.customer_id == payload.customer_id)
        .first()
    )
    if customer_exists is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    property_row = (
        db.query(Property.property_id, Property.customer_id)
        .filter(Property.property_id == payload.property_id)
        .first()
    )
    if property_row is None:
        raise HTTPException(status_code=404, detail="Property not found")

    if property_row.customer_id != payload.customer_id:
        raise HTTPException(
            status_code=400,
            detail="Property does not belong to the given customer_id",
        )

    new_invoice = Invoice(
        customer_id=payload.customer_id,
        property_id=payload.property_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        status=payload.status,
        issued_date=payload.issued_date,
        due_date=payload.due_date,
        subtotal=payload.subtotal,
        tax=payload.tax,
        total=payload.total,
        notes=payload.notes,
    )

    try:
        db.add(new_invoice)
        db.commit()
        db.refresh(new_invoice)
        return new_invoice

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Database constraint violation")
