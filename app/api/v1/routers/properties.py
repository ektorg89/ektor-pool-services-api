from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Customer, Property
from app.schemas.schemas import PropertyCreate, PropertyOut

router = APIRouter()


@router.get("", response_model=list[PropertyOut])
def list_properties(
    customer_id: Optional[int] = Query(default=None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Property)

    if customer_id is not None:
        q = q.filter(Property.customer_id == customer_id)

    return q.order_by(Property.property_id.desc()).limit(50).all()


@router.post("", response_model=PropertyOut, status_code=201)
def create_property(payload: PropertyCreate, db: Session = Depends(get_db)):
    customer_exists = (
        db.query(Customer.customer_id)
        .filter(Customer.customer_id == payload.customer_id)
        .first()
    )
    if customer_exists is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    new_property = Property(
    customer_id=payload.customer_id,
    label=payload.label,
    address1=payload.address1,
    address2=payload.address2,
    city=payload.city,
    state=payload.state,
    postal_code=payload.postal_code,
    notes=payload.notes,
    is_active=payload.is_active,
)

    try:
        db.add(new_property)
        db.commit()
        db.refresh(new_property)
        return new_property
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Database constraint violation")


@router.get("/{property_id}", response_model=PropertyOut)
def get_property(
    property_id: int = Path(..., ge=1, le=100, description="Property ID (1-100)"),
    db: Session = Depends(get_db),
):
    row = db.query(Property).filter(Property.property_id == property_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return row
