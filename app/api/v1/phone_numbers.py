import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.database import get_db
from app.models.phone_number import PhoneNumber
from app.schemas.phone_number import (
    PhoneNumberCreate,
    PhoneNumberRead,
    PhoneNumberUpdate,
    WebhookRegenerateResponse,
    WebhookUrlResponse,
)
from app.schemas.serializers import phone_number_to_read
from app.services.phone_numbers import (
    PhoneNumberServiceError,
    create_phone_number,
    regenerate_webhook,
    update_phone_number,
)
from app.services.webhook_url import build_inbound_webhook_url, build_webhook_url_prefix

router = APIRouter(tags=["phone-numbers"])


@router.post(
    "/companies/{company_id}/phone-numbers",
    response_model=PhoneNumberRead,
    status_code=status.HTTP_201_CREATED,
)
def create_phone_number_endpoint(
    _: Annotated[dict, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    company_id: uuid.UUID,
    body: PhoneNumberCreate,
) -> PhoneNumberRead:
    try:
        phone, token_plain = create_phone_number(db, company_id=company_id, data=body)
    except PhoneNumberServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return phone_number_to_read(phone, token_plain=token_plain)


@router.get("/companies/{company_id}/phone-numbers", response_model=list[PhoneNumberRead])
def list_phone_numbers(
    _: Annotated[dict, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    company_id: uuid.UUID,
) -> list[PhoneNumberRead]:
    rows = (
        db.query(PhoneNumber)
        .filter(PhoneNumber.company_id == company_id)
        .order_by(PhoneNumber.created_at.desc())
        .all()
    )
    return [phone_number_to_read(p) for p in rows]


@router.get("/companies/{company_id}/phone-numbers/{phone_number_id}", response_model=PhoneNumberRead)
def get_phone_number(
    _: Annotated[dict, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    company_id: uuid.UUID,
    phone_number_id: uuid.UUID,
) -> PhoneNumberRead:
    phone = (
        db.query(PhoneNumber)
        .filter(PhoneNumber.id == phone_number_id, PhoneNumber.company_id == company_id)
        .first()
    )
    if not phone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Número não encontrado.")
    return phone_number_to_read(phone)


@router.patch("/companies/{company_id}/phone-numbers/{phone_number_id}", response_model=PhoneNumberRead)
def patch_phone_number(
    _: Annotated[dict, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    company_id: uuid.UUID,
    phone_number_id: uuid.UUID,
    body: PhoneNumberUpdate,
) -> PhoneNumberRead:
    try:
        phone = update_phone_number(db, company_id=company_id, phone_number_id=phone_number_id, data=body)
    except PhoneNumberServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    if not phone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Número não encontrado.")
    return phone_number_to_read(phone)


@router.get(
    "/companies/{company_id}/phone-numbers/{phone_number_id}/webhook",
    response_model=WebhookUrlResponse,
)
def get_webhook_info(
    _: Annotated[dict, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    company_id: uuid.UUID,
    phone_number_id: uuid.UUID,
) -> WebhookUrlResponse:
    phone = (
        db.query(PhoneNumber)
        .filter(PhoneNumber.id == phone_number_id, PhoneNumber.company_id == company_id)
        .first()
    )
    if not phone or not phone.webhook_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook não encontrado.")
    prefix = build_webhook_url_prefix(company_id=company_id, phone_number_id=phone_number_id)
    return WebhookUrlResponse(
        phone_number_id=phone_number_id,
        company_id=company_id,
        webhook_url=None,
        webhook_url_prefix=prefix,
        message=(
            "O token secreto não é armazenado em texto claro. "
            "Use a URL completa retornada na criação do número ou chame o endpoint de regeneração."
        ),
    )


@router.post(
    "/companies/{company_id}/phone-numbers/{phone_number_id}/webhook/regenerate",
    response_model=WebhookRegenerateResponse,
)
def regenerate_webhook_nested(
    _: Annotated[dict, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    company_id: uuid.UUID,
    phone_number_id: uuid.UUID,
) -> WebhookRegenerateResponse:
    result = regenerate_webhook(db, company_id=company_id, phone_number_id=phone_number_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Número ou webhook não encontrado.")
    phone, token_plain = result
    url = build_inbound_webhook_url(
        company_id=phone.company_id,
        phone_number_id=phone.id,
        token=token_plain,
    )
    return WebhookRegenerateResponse(phone_number_id=phone.id, company_id=phone.company_id, webhook_url=url)


@router.post("/phone-numbers/{phone_number_id}/webhook/regenerate", response_model=WebhookRegenerateResponse)
def regenerate_webhook_flat(
    _: Annotated[dict, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    phone_number_id: uuid.UUID,
) -> WebhookRegenerateResponse:
    phone = db.get(PhoneNumber, phone_number_id)
    if not phone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Número não encontrado.")
    result = regenerate_webhook(db, company_id=phone.company_id, phone_number_id=phone_number_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook não encontrado.")
    phone, token_plain = result
    url = build_inbound_webhook_url(
        company_id=phone.company_id,
        phone_number_id=phone.id,
        token=token_plain,
    )
    return WebhookRegenerateResponse(phone_number_id=phone.id, company_id=phone.company_id, webhook_url=url)
