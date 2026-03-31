from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, LargeBinary, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.phone_number import PhoneNumber


class WebhookConfig(Base):
    __tablename__ = "webhook_configs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    phone_number_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("phone_numbers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    token_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    phone_number: Mapped["PhoneNumber"] = relationship("PhoneNumber", back_populates="webhook_config")


class WebhookEventLog(Base):
    __tablename__ = "webhook_event_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    webhook_config_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("webhook_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_body: Mapped[dict | list | str | None] = mapped_column(JSON, nullable=True)
    headers_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)

    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    webhook_config: Mapped[WebhookConfig] = relationship("WebhookConfig")
