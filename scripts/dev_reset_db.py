from __future__ import annotations

"""Developer utility to reset the local database schema.

WARNING: This drops all tables defined in SQLAlchemy metadata.
Use only in local/dev environments.
"""

from app import models as core_models
import os

from sqlalchemy import text

from app.db import ensure_pg_extensions, ensure_indexes, engine

# Import modules to register their tables with Base metadata.
from app.modules.cases import models as cases_models  # noqa: F401
from app.modules.pia import models as pia_models  # noqa: F401
from app.modules.tenant import models as tenant_models  # noqa: F401
from app.modules.users import models as users_models  # noqa: F401
from app.modules.dwf import models as dwf_models  # noqa: F401


def main() -> None:
    ensure_pg_extensions()
    core_models.Base.metadata.drop_all(bind=engine)
    core_models.Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL
                )
                """
            )
        )
        revision = os.getenv("ALEMBIC_HEAD", "0003_insider_program")
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:rev)"),
            {"rev": revision},
        )
    try:
        ensure_indexes()
    except Exception:
        # Index creation is best-effort in dev.
        pass


if __name__ == "__main__":
    main()
