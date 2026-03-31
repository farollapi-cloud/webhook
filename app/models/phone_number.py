from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.webhook import WebhookConfig


class WebhookProvider(str, enum.Enum):
    uazapi = "uazapi"


class PhoneConnectionStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    pending = "pending"
    error = "error"


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"
    __table_args__ = (UniqueConstraint("company_id", "phone_e164", name="uq_phone_company_e164"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_e164: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default=WebhookProvider.uazapi.value)
    uazapi_base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    uazapi_instance_token: Mapped[str] = mapped_column(Text, nullable=False)
    connection_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=PhoneConnectionStatus.active.value
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="phone_numbers")
    webhook_config: Mapped["WebhookConfig | None"] = relationship(
        "WebhookConfig", back_populates="phone_number", uselist=False, cascade="all, delete-orphan"
    )
