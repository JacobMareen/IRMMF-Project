"""Bootstrap helpers for app startup."""
from __future__ import annotations

import logging

from sqlalchemy import inspect

from app.core.registry import ModuleRegistry, ModuleSpec
from app.db import ensure_indexes, ensure_pg_extensions, engine
from app import models

logger = logging.getLogger(__name__)


def register_modules() -> ModuleRegistry:
    registry = ModuleRegistry()
    registry.register(ModuleSpec(
        key="assessment",
        label="Assessments",
        description="IRMMF assessment workflow, scoring, and reporting.",
    ))
    registry.register(ModuleSpec(
        key="dwf",
        label="Dynamic Workforce",
        description="DWF extension module with its own question bank and scoring.",
    ))
    registry.register(ModuleSpec(
        key="pia",
        label="Case Management",
        description="Procedural compliance workflow for Belgian Private Investigations Act 2024.",
    ))
    registry.register(ModuleSpec(
        key="cases",
        label="Investigations",
        description="Core case object, lifecycle status, evidence register, and task checklists.",
    ))
    registry.register(ModuleSpec(
        key="insider_program",
        label="Insider Risk Program",
        description="Policy governance, control register, and program actions linked to assessments.",
    ))
    return registry


def init_database() -> None:
    """Initialize tables and best-effort indexes for local/dev."""
    ensure_pg_extensions()
    metadata = models.Base.metadata
    with engine.begin() as conn:
        inspector = inspect(conn)
        users_columns: set[str] = set()
        if inspector.has_table("users"):
            users_columns = {col["name"] for col in inspector.get_columns("users")}
        for table in metadata.sorted_tables:
            if table.name == "user_roles" and "id" not in users_columns:
                # Skip user_roles when the legacy users table uses user_id instead of id.
                logger.warning("Skipping user_roles table creation due to legacy users schema.")
                continue
            try:
                table.create(bind=conn, checkfirst=True)
            except Exception as exc:
                # Continue startup even if a legacy table conflicts with current metadata.
                logger.warning("Skipping table %s due to create error: %s", table.name, exc)
    try:
        ensure_indexes()
    except Exception:
        # Index creation is best-effort in dev; migrations should own this in prod.
        pass
