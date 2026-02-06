"""Add registration audit metadata.

Revision ID: 0009_registration_audit
Revises: 0008_lead_attribution
Create Date: 2026-02-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0009_registration_audit"
down_revision = "0008_lead_attribution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("registered_ip", sa.String(45), nullable=True))
    op.add_column("users", sa.Column("registered_user_agent", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "registered_user_agent")
    op.drop_column("users", "registered_ip")
