"""Triage inbox tickets.

Revision ID: 0006_triage_inbox
Revises: 0005_case_expert_access
Create Date: 2026-02-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0006_triage_inbox"
down_revision = "0005_case_expert_access"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_triage_tickets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ticket_id", sa.String(64), nullable=False),
        sa.Column("tenant_key", sa.String(64), nullable=False),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("reporter_name", sa.String(255), nullable=True),
        sa.Column("reporter_email", sa.String(255), nullable=True),
        sa.Column("source", sa.String(32), nullable=False, server_default="dropbox"),
        sa.Column("status", sa.String(32), nullable=False, server_default="new"),
        sa.Column("triage_notes", sa.Text(), nullable=True),
        sa.Column("linked_case_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["linked_case_id"], ["cases.case_id"]),
    )
    op.create_index("ix_case_triage_ticket_id", "case_triage_tickets", ["ticket_id"], unique=True)
    op.create_index("ix_case_triage_tenant", "case_triage_tickets", ["tenant_key"])


def downgrade() -> None:
    op.drop_index("ix_case_triage_tenant", table_name="case_triage_tickets")
    op.drop_index("ix_case_triage_ticket_id", table_name="case_triage_tickets")
    op.drop_table("case_triage_tickets")
