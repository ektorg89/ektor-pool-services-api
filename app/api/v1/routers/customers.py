from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Customer
from app.schemas.schemas import CustomerCreate, CustomerOut, CustomerUpdate

router = APIRouter()


@router.get("", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).order_by(Customer.customer_id.desc()).limit(50).all()


@router.post("", response_model=CustomerOut, status_code=201)
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


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int = Path(..., ge=1, le=100, description="Customer ID (1-100)"),
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer

@router.delete("/{customer_id}", status_code=204)
def delete_customer(
    customer_id: int = Path(..., ge=1, le=100, description="Customer ID (1-100)"),
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    try:
        db.delete(customer)
        db.commit()
        return None

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Customer cannot be deleted due to references")
    
@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    payload: CustomerUpdate,
    customer_id: int = Path(..., ge=1, le=100, description="Customer ID (1-100)"),
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    updated = False

    if payload.first_name is not None:
        customer.first_name = payload.first_name
        updated = True

    if payload.last_name is not None:
        customer.last_name = payload.last_name
        updated = True

    if not updated:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    try:
        db.commit()
        db.refresh(customer)
        return customer

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Database constraint violation")
    
@router.put("/{customer_id}", response_model=CustomerOut)
def replace_customer(
    customer_id: int = Path(..., ge=1, le=100, description="Customer ID (1-100)"),
    payload: CustomerCreate = None,  # FastAPI lo tratará como body
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer.first_name = payload.first_name
    customer.last_name = payload.last_name

    try:
        db.commit()
        db.refresh(customer)
        return customer

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Database constraint violation")