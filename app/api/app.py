import os
from decimal import Decimal
from datetime import date
from typing import Optional

from fastapi import FastAPI, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.models import Customer, Invoice, Property
from app.schemas.schemas import (
    CustomerOut,
    CustomerCreate,
    InvoiceOut,
    InvoiceCreate,
    CustomerStatementOut,
    StatementItem,
)

app = FastAPI(title="Ektor Pool Services API")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": os.getenv("APP_VERSION", "unknown"),
    }


@app.get("/reports/customers/{customer_id}/statement", response_model=CustomerStatementOut)
def customer_statement(
    customer_id: int = Path(..., ge=1, description="Customer ID (>= 1)"),
    from_: date = Query(..., alias="from", description="Start date (YYYY-MM-DD)"),
    to: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    if from_ > to:
        raise HTTPException(status_code=400, detail="'from' must be <= 'to'")

    customer_exists = (
        db.query(Customer.customer_id)
        .filter(Customer.customer_id == customer_id)
        .first()
    )
    if customer_exists is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    invoices = (
        db.query(Invoice)
        .filter(Invoice.customer_id == customer_id)
        .filter(Invoice.issued_date >= from_)
        .filter(Invoice.issued_date <= to)
        .order_by(Invoice.issued_date.asc(), Invoice.invoice_id.asc())
        .all()
    )

    total = sum((inv.total for inv in invoices), Decimal("0.00"))

    items = [
        StatementItem(
            invoice_id=inv.invoice_id,
            issued_date=inv.issued_date,
            status=inv.status,
            total=inv.total,
        )
        for inv in invoices
    ]

    return CustomerStatementOut(
        customer_id=customer_id,
        from_date=from_,
        to_date=to,
        total=total,
        items=items,
    )


@app.get("/customers", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).order_by(Customer.customer_id.desc()).limit(50).all()


@app.post("/customers", response_model=CustomerOut, status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    try:
        new_customer = Customer(
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        return new_customer

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Database constraint violation")


@app.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int = Path(..., ge=1, le=100, description="Customer ID (1-100)"),
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


@app.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(
    status: Optional[str] = Query(
        default=None,
        pattern="^(draft|sent|paid|void)$",
        description="Filter by invoice status: draft, sent, paid, void",
    ),
    customer_id: Optional[int] = Query(
        default=None,
        ge=1,
        le=100,
        description="Filter by customer_id (1 to 100 — small business scope)",
    ),
    property_id: Optional[int] = Query(
        default=None,
        ge=1,
        le=100,
        description="Filter by property_id (1 to 100 — small business scope)",
    ),
    from_date: Optional[date] = Query(
        default=None,
        description="Filter invoices issued on/after this date (YYYY-MM-DD)",
    ),
    to_date: Optional[date] = Query(
        default=None,
        description="Filter invoices issued on/before this date (YYYY-MM-DD)",
    ),
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


@app.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int = Path(..., ge=1, description="Invoice ID (>= 1)"),
    db: Session = Depends(get_db),
):
    invoice = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()

    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return invoice


@app.post("/invoices", response_model=InvoiceOut, status_code=201)
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
