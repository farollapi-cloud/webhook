import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))


def _cors_allow_origins() -> list[str]:
    raw = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
    if raw:
        return raw
    if settings.environment == "development":
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    return []


app = FastAPI(
    title="Webhook SaaS",
    version="0.1.0",
    description="Multiempresa: empresas, números WhatsApp (Uazapi) e recepção de webhooks.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
