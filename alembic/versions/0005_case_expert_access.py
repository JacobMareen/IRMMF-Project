"""Case expert access grants.

Revision ID: 0005_case_expert_access
Revises: 0004_insider_program_roadmap
Create Date: 2026-02-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0005_case_expert_access"
down_revision = "0004_insider_program_roadmap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_expert_access",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("access_id", sa.String(64), nullable=False),
        sa.Column("expert_email", sa.String(255), nullable=False),
        sa.Column("expert_name", sa.String(255), nullable=True),
        sa.Column("organization", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("granted_by", sa.String(128), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", sa.String(128), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"]),
    )
    op.create_index("ix_case_expert_access_case_id", "case_expert_access", ["case_id"])
    op.create_index("ix_case_expert_access_access_id", "case_expert_access", ["access_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_case_expert_access_access_id", table_name="case_expert_access")
    op.drop_index("ix_case_expert_access_case_id", table_name="case_expert_access")
    op.drop_table("case_expert_access")
