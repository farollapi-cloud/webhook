import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.config import get_settings
from app.database import get_db
from app.services.inbound_webhook import receive_uazapi_webhook
from sqlalchemy.orm import Session

router = APIRouter(prefix="/webhooks/whatsapp", tags=["webhooks-inbound"])


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.api_route(
    "/{company_id}/{phone_number_id}/{token}",
    methods=["GET", "POST", "PUT", "PATCH"],
    response_model=None,
)
async def uazapi_inbound(
    request: Request,
    company_id: uuid.UUID,
    phone_number_id: uuid.UUID,
    token: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    settings = get_settings()
    cl = request.headers.get("content-length")
    if cl and cl.isdigit() and int(cl) > settings.webhook_max_body_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Payload grande demais.")

    body = await request.body()
    if len(body) > settings.webhook_max_body_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Payload grande demais.")

    headers = {k: v for k, v in request.headers.items()}
    ct = request.headers.get("content-type")

    ok, _ = receive_uazapi_webhook(
        db,
        company_id=company_id,
        phone_number_id=phone_number_id,
        token=token,
        raw_body=body,
        content_type=ct,
        headers=headers,
        client_ip=_client_ip(request),
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return Response(
        content='{"received":true}',
        status_code=status.HTTP_200_OK,
        media_type="application/json",
    )
