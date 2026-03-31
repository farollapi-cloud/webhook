import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.config import get_settings


def generate_webhook_token() -> str:
    return secrets.token_urlsafe(32)


def hash_webhook_token(token: str) -> bytes:
    return hashlib.sha256(token.encode("utf-8")).digest()


def verify_webhook_token(token: str, stored_hash: bytes) -> bool:
    if len(stored_hash) != 32:
        return False
    candidate = hashlib.sha256(token.encode("utf-8")).digest()
    return hmac.compare_digest(candidate, stored_hash)


def create_access_token(*, subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
