from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.schemas.auth import TokenRequest, TokenResponse
from app.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
def issue_token(body: TokenRequest) -> TokenResponse:
    settings = get_settings()
    if body.client_id != settings.auth_client_id or body.client_secret != settings.auth_client_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")
    token = create_access_token(subject=body.client_id, extra_claims={"role": "admin"})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
    )
