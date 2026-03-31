import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.phone_number import PhoneConnectionStatus, WebhookProvider


E164_REGEX = r"^\+[1-9]\d{1,14}$"


class PhoneNumberCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    phone_e164: str = Field(..., pattern=E164_REGEX, description="E.164, ex: +5511999999999")
    provider: WebhookProvider = WebhookProvider.uazapi
    uazapi_base_url: str = Field(..., min_length=8, max_length=512)
    uazapi_instance_token: str = Field(..., min_length=1)
    connection_status: PhoneConnectionStatus = PhoneConnectionStatus.active


class PhoneNumberUpdate(BaseModel):
    label: str | None = Field(None, min_length=1, max_length=255)
    phone_e164: str | None = Field(None, pattern=E164_REGEX)
    provider: WebhookProvider | None = None
    uazapi_base_url: str | None = Field(None, min_length=8, max_length=512)
    uazapi_instance_token: str | None = Field(None, min_length=1)
    connection_status: PhoneConnectionStatus | None = None


class PhoneNumberRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    label: str
    phone_e164: str
    provider: str
    uazapi_base_url: str
    connection_status: str
    webhook_url: str | None = None
    webhook_url_prefix: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookUrlResponse(BaseModel):
    phone_number_id: uuid.UUID
    company_id: uuid.UUID
    webhook_url: str | None = None
    webhook_url_prefix: str
    message: str | None = None


class WebhookRegenerateResponse(BaseModel):
    phone_number_id: uuid.UUID
    company_id: uuid.UUID
    webhook_url: str
    message: str = (
        "Atualize manualmente a URL do webhook no painel da Uazapi.dev; o token anterior foi invalidado."
    )
