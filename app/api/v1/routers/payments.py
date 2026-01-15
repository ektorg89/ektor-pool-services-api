from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.routers.auth import require_roles
from app.db.session import get_db
from app.models.models import Invoice, Payment
from app.schemas.schemas import PaymentCreate, PaymentOut

router = APIRouter()


@router.post(
    "",
    response_model=PaymentOut,
    status_code=201,
    operation_id="v1_payments_create",
    dependencies=[Depends(require_roles("admin"))],
)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.invoice_id == payload.invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status == "paid":
        raise HTTPException(status_code=409, detail="Invoice is already paid")

    if invoice.status == "void":
        raise HTTPException(status_code=400, detail="Cannot pay a void invoice")

    if payload.reference:
        dup = (
            db.query(Payment.payment_id)
            .filter(Payment.invoice_id == payload.invoice_id)
            .filter(Payment.reference == payload.reference)
            .first()
        )
        if dup is not None:
            raise HTTPException(
                status_code=409,
                detail="Duplicate payment reference for this invoice",
            )

    paid_so_far = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.invoice_id == invoice.invoice_id)
        .scalar()
    )

    if (Decimal(str(paid_so_far)) + payload.amount) > Decimal(str(invoice.total)):
        raise HTTPException(status_code=409, detail="Payment exceeds invoice total")

    new_payment = Payment(
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        paid_date=payload.paid_date,
        method=payload.method or "other",
        reference=payload.reference,
        notes=payload.notes,
    )

    try:
        db.add(new_payment)

        inv_total = Decimal(str(invoice.total))
        new_total_paid = Decimal(str(paid_so_far)) + Decimal(str(payload.amount))

        if new_total_paid >= inv_total:
            invoice.status = "paid"
        elif invoice.status == "draft":
            invoice.status = "sent"

        db.commit()
        db.refresh(new_payment)
        return new_payment

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Database constraint violation: {str(getattr(e, 'orig', e))}",
        )


@router.get(
    "",
    response_model=list[PaymentOut],
    operation_id="v1_payments_list",
)
def list_payments(
    invoice_id: int | None = Query(
        default=None,
        ge=1,
        description="Filter by invoice_id (>= 1)",
    ),
    db: Session = Depends(get_db),
):
    q = db.query(Payment)

    if invoice_id is not None:
        q = q.filter(Payment.invoice_id == invoice_id)

    return q.order_by(Payment.payment_id.desc()).limit(50).all()
