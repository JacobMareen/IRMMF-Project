"""Tenant settings columns + assessment tenant defaults.

Revision ID: 0002_tenant_settings_assessments
Revises: 0001_baseline
Create Date: 2026-01-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0002_tenant_settings_assessments"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


JURISDICTION_RULES_DEFAULT = (
    "{"
    '"BE":{"decision_deadline_days":3,"dismissal_deadline_days":3,'
    '"deadline_type":"working_days","requires_registered_mail_receipt":true},'
    '"NL":{"decision_deadline_hours":48,"deadline_type":"hours","requires_suspension_check":true},'
    '"LU":{"min_cooling_off_days":1,"max_dismissal_window_days":8,'
    '"trigger_event":"pre_dismissal_interview"},'
    '"IE":{"warn_if_decision_under_hours":24,"requires_appeal_checkbox":true}'
    "}"
)


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE IF EXISTS tenant_settings
            ADD COLUMN IF NOT EXISTS weekend_days jsonb NOT NULL DEFAULT '[5,6]'::jsonb,
            ADD COLUMN IF NOT EXISTS saturday_is_business_day boolean NOT NULL DEFAULT false,
            ADD COLUMN IF NOT EXISTS deadline_cutoff_hour integer NOT NULL DEFAULT 17,
            ADD COLUMN IF NOT EXISTS notifications_enabled boolean NOT NULL DEFAULT true,
            ADD COLUMN IF NOT EXISTS serious_cause_notifications_enabled boolean NOT NULL DEFAULT true,
            ADD COLUMN IF NOT EXISTS jurisdiction_rules jsonb NOT NULL DEFAULT '%s'::jsonb;
        """
        % JURISDICTION_RULES_DEFAULT
    )
    op.execute(
        """
        ALTER TABLE IF EXISTS assessments
            ALTER COLUMN tenant_key SET DEFAULT 'default';
        """
    )
    op.execute(
        """
        UPDATE assessments
        SET tenant_key = 'default'
        WHERE tenant_key IS NULL;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE IF EXISTS tenant_settings
            DROP COLUMN IF EXISTS weekend_days,
            DROP COLUMN IF EXISTS saturday_is_business_day,
            DROP COLUMN IF EXISTS deadline_cutoff_hour,
            DROP COLUMN IF EXISTS notifications_enabled,
            DROP COLUMN IF EXISTS serious_cause_notifications_enabled,
            DROP COLUMN IF EXISTS jurisdiction_rules;
        """
    )
    op.execute(
        """
        ALTER TABLE IF EXISTS assessments
            ALTER COLUMN tenant_key DROP DEFAULT;
        """
    )
