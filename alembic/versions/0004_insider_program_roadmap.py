"""Insider risk program roadmap items.

Revision ID: 0004_insider_program_roadmap
Revises: 0003_insider_program
Create Date: 2026-01-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_insider_program_roadmap"
down_revision = "0003_insider_program"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "insider_risk_roadmap_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_key", sa.String(128), nullable=False),
        sa.Column("phase", sa.String(32), nullable=False, server_default="Now"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(128), nullable=True),
        sa.Column("target_window", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="planned"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_insider_risk_roadmap_tenant_phase",
        "insider_risk_roadmap_items",
        ["tenant_key", "phase"],
    )


def downgrade() -> None:
    op.drop_index("ix_insider_risk_roadmap_tenant_phase", table_name="insider_risk_roadmap_items")
    op.drop_table("insider_risk_roadmap_items")
