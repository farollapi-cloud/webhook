from fastapi import APIRouter

from app.api.v1 import auth, companies, inbound, phone_numbers

api_v1 = APIRouter()
api_v1.include_router(auth.router)
api_v1.include_router(companies.router)
api_v1.include_router(phone_numbers.router)
api_v1.include_router(inbound.router)
