"""Add lead attribution fields.

Revision ID: 0008_lead_attribution
Revises: 0007_marketing_consent
Create Date: 2026-02-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0008_lead_attribution"
down_revision = "0007_marketing_consent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenant_settings", sa.Column("utm_campaign", sa.String(120), nullable=True))
    op.add_column("tenant_settings", sa.Column("utm_source", sa.String(120), nullable=True))
    op.add_column("tenant_settings", sa.Column("utm_medium", sa.String(120), nullable=True))


def downgrade() -> None:
    op.drop_column("tenant_settings", "utm_medium")
    op.drop_column("tenant_settings", "utm_source")
    op.drop_column("tenant_settings", "utm_campaign")
