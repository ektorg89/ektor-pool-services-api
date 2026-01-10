from fastapi import APIRouter

from app.api.v1.routers import customers

api_router = APIRouter()
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
