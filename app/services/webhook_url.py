import uuid

from app.config import get_settings


def build_inbound_webhook_url(*, company_id: uuid.UUID, phone_number_id: uuid.UUID, token: str) -> str:
    base = get_settings().backend_public_url.rstrip("/")
    return f"{base}/api/v1/webhooks/whatsapp/{company_id}/{phone_number_id}/{token}"


def build_webhook_url_prefix(*, company_id: uuid.UUID, phone_number_id: uuid.UUID) -> str:
    base = get_settings().backend_public_url.rstrip("/")
    return f"{base}/api/v1/webhooks/whatsapp/{company_id}/{phone_number_id}/"
