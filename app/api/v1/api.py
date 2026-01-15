from fastapi import APIRouter, Depends

from app.api.v1.routers.auth import get_current_user
from app.api.v1.routers import auth, customers, invoices, payments, properties

api_router = APIRouter()

protected_router = APIRouter(dependencies=[Depends(get_current_user)])

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

protected_router.include_router(customers.router, prefix="/customers", tags=["customers"])
protected_router.include_router(properties.router, prefix="/properties", tags=["properties"])
protected_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
protected_router.include_router(payments.router, prefix="/payments", tags=["payments"])

api_router.include_router(protected_router)
