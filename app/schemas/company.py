import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.company import CompanyStatus


class CompanyCreate(BaseModel):
    legal_name: str = Field(..., min_length=1, max_length=255)
    contact_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=3, max_length=32)
    status: CompanyStatus = CompanyStatus.active
    notes: str | None = None


class CompanyUpdate(BaseModel):
    legal_name: str | None = Field(None, min_length=1, max_length=255)
    contact_name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, min_length=3, max_length=32)
    status: CompanyStatus | None = None
    notes: str | None = None


class CompanyRead(BaseModel):
    id: uuid.UUID
    legal_name: str
    contact_name: str
    email: str
    phone: str
    status: CompanyStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
