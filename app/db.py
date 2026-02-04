"""Database wiring.

This project is still in alpha, so we keep configuration frictionless:

- Reads DATABASE_URL from the environment (preferred)
- Falls back to a local Postgres default suitable for development

Example:
    export DATABASE_URL='postgresql+psycopg://localhost:5432/irmmf_db'
"""

from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine, text

from sqlalchemy.orm import declarative_base, sessionmaker


DEFAULT_DATABASE_URL = "postgresql+psycopg://localhost:5432/irmmf_db"


def _database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


engine = create_engine(
    _database_url(),
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    """FastAPI dependency."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_pg_extensions() -> None:
    """Ensure small Postgres conveniences exist (safe to run repeatedly)."""

    with engine.begin() as conn:
        # For gen_random_uuid() used in a few models.
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))


def ensure_indexes() -> None:
    """Create indexes used heavily by the UI filtering.

    SQLAlchemy won't auto-add indexes to existing tables without migrations.
    This helper keeps local dev fast.
    """

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_dim_questions_domain ON dim_questions(domain);
                CREATE INDEX IF NOT EXISTS ix_dim_questions_tier ON dim_questions(tier);
                CREATE INDEX IF NOT EXISTS ix_dim_questions_domain_tier ON dim_questions(domain, tier);
                CREATE INDEX IF NOT EXISTS ix_dim_answers_question_id ON dim_answers(question_id);
                CREATE INDEX IF NOT EXISTS ix_fact_responses_assessment_q_id ON fact_responses(assessment_id, q_id);
                CREATE INDEX IF NOT EXISTS ix_fact_responses_assessment_id ON fact_responses(assessment_id);
                CREATE INDEX IF NOT EXISTS ix_fact_intake_responses_assessment_id ON fact_intake_responses(assessment_id);

                -- Recommendation table indexes (GIN for array fields)
                CREATE INDEX IF NOT EXISTS ix_dim_recs_category ON dim_recommendations(category);
                CREATE INDEX IF NOT EXISTS ix_dim_recs_target_axes ON dim_recommendations USING GIN(target_axes);
                CREATE INDEX IF NOT EXISTS ix_dim_recs_scenarios ON dim_recommendations USING GIN(relevant_scenarios);
                CREATE INDEX IF NOT EXISTS ix_fact_assessment_recs_status ON fact_assessment_recommendations(status);
                CREATE INDEX IF NOT EXISTS ix_fact_assessment_recs_priority ON fact_assessment_recommendations(priority);
                """
            )
        )


def ensure_audit_immutability() -> None:
    """Best-effort guardrails to keep audit logs append-only in dev."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE OR REPLACE FUNCTION prevent_audit_mutation()
                RETURNS trigger AS $$
                BEGIN
                    RAISE EXCEPTION 'Audit logs are append-only';
                END;
                $$ LANGUAGE plpgsql;
                """
            )
        )
        conn.execute(
            text(
                """
                DO $$
                BEGIN
                    IF to_regclass('public.case_audit_events') IS NOT NULL THEN
                        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_case_audit_immutable') THEN
                            CREATE TRIGGER trg_case_audit_immutable
                            BEFORE UPDATE OR DELETE ON case_audit_events
                            FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();
                        END IF;
                    END IF;
                    IF to_regclass('public.pia_audit_events') IS NOT NULL THEN
                        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_pia_audit_immutable') THEN
                            CREATE TRIGGER trg_pia_audit_immutable
                            BEFORE UPDATE OR DELETE ON pia_audit_events
                            FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();
                        END IF;
                    END IF;
                END $$;
                """
            )
        )
