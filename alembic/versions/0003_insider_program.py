"""Insider risk program policy + controls.

Revision ID: 0003_insider_program
Revises: 0002_tenant_settings_assessments
Create Date: 2026-01-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_insider_program"
down_revision = "0002_tenant_settings_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "insider_risk_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, server_default="Draft"),
        sa.Column("version", sa.String(32), nullable=False, server_default="v1.0"),
        sa.Column("owner", sa.String(128), nullable=True),
        sa.Column("approval", sa.String(128), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("last_reviewed", sa.Date(), nullable=True),
        sa.Column("next_review", sa.Date(), nullable=True),
        sa.Column("principles", postgresql.JSONB(), nullable=True),
        sa.Column("sections", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_key", name="uq_insider_risk_policy_tenant"),
    )
    op.create_index(
        "ix_insider_risk_policies_tenant_key",
        "insider_risk_policies",
        ["tenant_key"],
    )

    op.create_table(
        "insider_risk_controls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_key", sa.String(128), nullable=False),
        sa.Column("control_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("domain", sa.String(64), nullable=False),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="planned"),
        sa.Column("owner", sa.String(128), nullable=True),
        sa.Column("frequency", sa.String(64), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("last_reviewed", sa.Date(), nullable=True),
        sa.Column("next_review", sa.Date(), nullable=True),
        sa.Column("linked_actions", postgresql.JSONB(), nullable=True),
        sa.Column("linked_rec_ids", postgresql.JSONB(), nullable=True),
        sa.Column("linked_categories", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_key", "control_id", name="uq_insider_risk_control_tenant"),
    )
    op.create_index(
        "ix_insider_risk_controls_tenant_domain",
        "insider_risk_controls",
        ["tenant_key", "domain"],
    )


def downgrade() -> None:
    op.drop_index("ix_insider_risk_controls_tenant_domain", table_name="insider_risk_controls")
    op.drop_table("insider_risk_controls")
    op.drop_index("ix_insider_risk_policies_tenant_key", table_name="insider_risk_policies")
    op.drop_table("insider_risk_policies")
