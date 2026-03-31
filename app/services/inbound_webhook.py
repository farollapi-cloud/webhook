import json
import uuid
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.company import Company, CompanyStatus
from app.models.phone_number import PhoneConnectionStatus, PhoneNumber
from app.models.webhook import WebhookConfig, WebhookEventLog
from app.security import verify_webhook_token


def receive_uazapi_webhook(
    db: Session,
    *,
    company_id: uuid.UUID,
    phone_number_id: uuid.UUID,
    token: str,
    raw_body: bytes,
    content_type: str | None,
    headers: dict[str, str],
    client_ip: str | None,
) -> tuple[bool, str | None]:
    """Valida e persiste evento. Retorna (sucesso, motivo_erro_interno)."""

    phone = (
        db.query(PhoneNumber)
        .options(joinedload(PhoneNumber.webhook_config), joinedload(PhoneNumber.company))
        .filter(PhoneNumber.id == phone_number_id, PhoneNumber.company_id == company_id)
        .first()
    )
    if not phone:
        return False, "not_found"

    if not phone.webhook_config:
        return False, "no_config"

    cfg: WebhookConfig = phone.webhook_config
    if not cfg.active:
        return False, "inactive"

    if not verify_webhook_token(token, cfg.token_hash):
        return False, "bad_token"

    company: Company = phone.company
    if company.status in (CompanyStatus.inactive.value, CompanyStatus.suspended.value):
        return False, "company_inactive"

    if phone.connection_status == PhoneConnectionStatus.inactive.value:
        return False, "phone_inactive"

    parsed: dict[str, Any] | list[Any] | str | None
    try:
        text = raw_body.decode("utf-8")
        parsed = json.loads(text) if text.strip() else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        parsed = {"_raw_base64": raw_body.hex()}

    log = WebhookEventLog(
        webhook_config_id=cfg.id,
        raw_body=parsed if isinstance(parsed, (dict, list)) else {"_text": parsed},
        headers_snapshot=headers,
        client_ip=client_ip,
        content_type=content_type,
    )
    db.add(log)
    db.commit()
    return True, None
