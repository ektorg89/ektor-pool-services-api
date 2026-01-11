from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Invoice, Payment
from app.schemas.schemas import PaymentCreate, PaymentOut

router = APIRouter()


@router.post("", response_model=PaymentOut, status_code=201)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.invoice_id == payload.invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Regla simple: no permitir pagos en invoices void
    if invoice.status == "void":
        raise HTTPException(status_code=400, detail="Cannot pay a void invoice")

    new_payment = Payment(
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        paid_date=payload.paid_date,
        method=payload.method,
        reference=payload.reference,
        notes=payload.notes,
    )

    try:
        db.add(new_payment)

        # Si con este pago queda saldada o sobrepagada => paid
        # (Como no tenemos balance formal todavía, usamos subtotal+tax como total)
        inv_total = Decimal(str(invoice.total))
        paid_sum = (
            db.query(Payment)
            .with_entities(Payment.amount)
            .filter(Payment.invoice_id == payload.invoice_id)
            .all()
        )
        already_paid = sum((Decimal(str(x[0])) for x in paid_sum), Decimal("0.00"))
        new_total_paid = already_paid + Decimal(str(payload.amount))

        if new_total_paid >= inv_total:
            invoice.status = "paid"
        elif invoice.status == "draft":
            invoice.status = "sent"

        db.commit()
        db.refresh(new_payment)
        return new_payment

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Database constraint violation")
