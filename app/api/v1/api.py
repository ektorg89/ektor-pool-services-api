from fastapi import APIRouter

from app.api.v1.routers import customers, invoices, properties

api_router = APIRouter()
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
