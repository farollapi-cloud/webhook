import logging

from fastapi import FastAPI

from app.api.v1.router import api_v1
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

app = FastAPI(
    title="Webhook SaaS",
    version="0.1.0",
    description="Multiempresa: empresas, números WhatsApp (Uazapi) e recepção de webhooks.",
)

app.include_router(api_v1, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
