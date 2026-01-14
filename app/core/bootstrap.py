"""Bootstrap helpers for app startup."""
from __future__ import annotations

from app.core.registry import ModuleRegistry, ModuleSpec
from app.db import ensure_pg_extensions, ensure_indexes, engine
from app import models


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
    return registry


def init_database() -> None:
    """Initialize tables and best-effort indexes for local/dev."""
    ensure_pg_extensions()
    models.Base.metadata.create_all(bind=engine)
    try:
        ensure_indexes()
    except Exception:
        # Index creation is best-effort in dev; migrations should own this in prod.
        pass
