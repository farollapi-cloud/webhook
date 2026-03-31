from app.models.phone_number import PhoneNumber
from app.schemas.phone_number import PhoneNumberRead
from app.services.webhook_url import build_inbound_webhook_url, build_webhook_url_prefix


def phone_number_to_read(phone: PhoneNumber, *, token_plain: str | None = None) -> PhoneNumberRead:
    prefix = build_webhook_url_prefix(company_id=phone.company_id, phone_number_id=phone.id)
    url = (
        build_inbound_webhook_url(
            company_id=phone.company_id,
            phone_number_id=phone.id,
            token=token_plain,
        )
        if token_plain
        else None
    )
    return PhoneNumberRead(
        id=phone.id,
        company_id=phone.company_id,
        label=phone.label,
        phone_e164=phone.phone_e164,
        provider=phone.provider,
        uazapi_base_url=phone.uazapi_base_url,
        connection_status=phone.connection_status,
        webhook_url=url,
        webhook_url_prefix=prefix,
        created_at=phone.created_at,
        updated_at=phone.updated_at,
    )
