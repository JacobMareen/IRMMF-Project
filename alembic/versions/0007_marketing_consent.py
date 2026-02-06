"""Add marketing consent fields.

Revision ID: 0007_marketing_consent
Revises: 0006_triage_inbox
Create Date: 2026-02-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0007_marketing_consent"
down_revision = "0006_triage_inbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenant_settings",
        sa.Column("marketing_consent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("marketing_consent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("marketing_consent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "marketing_consent_at")
    op.drop_column("users", "marketing_consent")
    op.drop_column("tenant_settings", "marketing_consent")
