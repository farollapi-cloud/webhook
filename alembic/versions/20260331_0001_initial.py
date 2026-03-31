"""initial tables

Revision ID: 20260331_0001
Revises:
Create Date: 2026-03-31

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260331_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("contact_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_companies_email"), "companies", ["email"], unique=False)

    op.create_table(
        "phone_numbers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("phone_e164", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("uazapi_base_url", sa.String(length=512), nullable=False),
        sa.Column("uazapi_instance_token", sa.Text(), nullable=False),
        sa.Column("connection_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "phone_e164", name="uq_phone_company_e164"),
    )
    op.create_index(op.f("ix_phone_numbers_company_id"), "phone_numbers", ["company_id"], unique=False)
    op.create_index(op.f("ix_phone_numbers_phone_e164"), "phone_numbers", ["phone_e164"], unique=False)

    op.create_table(
        "webhook_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("phone_number_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["phone_number_id"], ["phone_numbers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_number_id"),
    )
    op.create_index(op.f("ix_webhook_configs_phone_number_id"), "webhook_configs", ["phone_number_id"], unique=True)

    op.create_table(
        "webhook_event_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("webhook_config_id", sa.Uuid(), nullable=False),
        sa.Column("raw_body", sa.JSON(), nullable=True),
        sa.Column("headers_snapshot", sa.JSON(), nullable=True),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["webhook_config_id"], ["webhook_configs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_webhook_event_logs_webhook_config_id"), "webhook_event_logs", ["webhook_config_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_webhook_event_logs_webhook_config_id"), table_name="webhook_event_logs")
    op.drop_table("webhook_event_logs")
    op.drop_index(op.f("ix_webhook_configs_phone_number_id"), table_name="webhook_configs")
    op.drop_table("webhook_configs")
    op.drop_index(op.f("ix_phone_numbers_phone_e164"), table_name="phone_numbers")
    op.drop_index(op.f("ix_phone_numbers_company_id"), table_name="phone_numbers")
    op.drop_table("phone_numbers")
    op.drop_index(op.f("ix_companies_email"), table_name="companies")
    op.drop_table("companies")
