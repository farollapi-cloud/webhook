import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.company import Company, CompanyStatus
from app.models.phone_number import PhoneConnectionStatus, PhoneNumber
from app.models.webhook import WebhookConfig
from app.schemas.phone_number import PhoneNumberCreate, PhoneNumberUpdate
from app.security import generate_webhook_token, hash_webhook_token
from app.services.webhook_url import build_inbound_webhook_url


class PhoneNumberServiceError(Exception):
    pass


def _company_active(company: Company) -> None:
    if company.status in (CompanyStatus.inactive.value, CompanyStatus.suspended.value):
        raise PhoneNumberServiceError("Empresa inativa ou suspensa.")


def create_phone_number(
    db: Session,
    *,
    company_id: uuid.UUID,
    data: PhoneNumberCreate,
) -> tuple[PhoneNumber, str]:
    company = db.get(Company, company_id)
    if not company:
        raise PhoneNumberServiceError("Empresa não encontrada.")
    _company_active(company)

    token_plain = generate_webhook_token()
    token_hash = hash_webhook_token(token_plain)

    phone = PhoneNumber(
        company_id=company_id,
        label=data.label,
        phone_e164=data.phone_e164,
        provider=data.provider.value,
        uazapi_base_url=data.uazapi_base_url,
        uazapi_instance_token=data.uazapi_instance_token,
        connection_status=data.connection_status.value,
    )
    db.add(phone)
    db.flush()

    cfg = WebhookConfig(phone_number_id=phone.id, token_hash=token_hash, active=True)
    db.add(cfg)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise PhoneNumberServiceError("Número duplicado para esta empresa ou violação de restrição.") from e

    db.refresh(phone)
    return phone, token_plain


def update_phone_number(
    db: Session,
    *,
    company_id: uuid.UUID,
    phone_number_id: uuid.UUID,
    data: PhoneNumberUpdate,
) -> PhoneNumber | None:
    phone = (
        db.query(PhoneNumber)
        .filter(PhoneNumber.id == phone_number_id, PhoneNumber.company_id == company_id)
        .first()
    )
    if not phone:
        return None

    if data.label is not None:
        phone.label = data.label
    if data.phone_e164 is not None:
        phone.phone_e164 = data.phone_e164
    if data.provider is not None:
        phone.provider = data.provider.value
    if data.uazapi_base_url is not None:
        phone.uazapi_base_url = data.uazapi_base_url
    if data.uazapi_instance_token is not None:
        phone.uazapi_instance_token = data.uazapi_instance_token
    if data.connection_status is not None:
        phone.connection_status = data.connection_status.value

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise PhoneNumberServiceError("Conflito ao atualizar número.") from None

    db.refresh(phone)
    return phone


def regenerate_webhook(
    db: Session,
    *,
    company_id: uuid.UUID,
    phone_number_id: uuid.UUID,
) -> tuple[PhoneNumber, str] | None:
    phone = (
        db.query(PhoneNumber)
        .filter(PhoneNumber.id == phone_number_id, PhoneNumber.company_id == company_id)
        .first()
    )
    if not phone or not phone.webhook_config:
        return None

    token_plain = generate_webhook_token()
    phone.webhook_config.token_hash = hash_webhook_token(token_plain)
    phone.webhook_config.active = True
    db.add(phone.webhook_config)
    db.commit()
    db.refresh(phone)
    return phone, token_plain


def public_webhook_url_for_phone(phone: PhoneNumber, token_plain: str | None) -> str | None:
    if not token_plain:
        return None
    return build_inbound_webhook_url(
        company_id=phone.company_id,
        phone_number_id=phone.id,
        token=token_plain,
    )
