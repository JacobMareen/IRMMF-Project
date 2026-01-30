from __future__ import annotations

"""Stamp the alembic_version table without the Alembic CLI.

Use this after applying migration SQL manually (or when Alembic isn't available).
"""

import argparse
import os
import sys

from sqlalchemy import text

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.db import engine  # noqa: E402

DEFAULT_REVISION = "0002_tenant_settings_assessments"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stamp alembic_version for manually applied migrations."
    )
    parser.add_argument(
        "--revision",
        default=DEFAULT_REVISION,
        help="Revision string to stamp (default: %(default)s)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing revision when it differs.",
    )
    args = parser.parse_args()

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
        current = conn.execute(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        ).scalar()
        if current:
            if current == args.revision:
                print(f"alembic_version already set to {current}")
                return
            if not args.force:
                raise SystemExit(
                    f"alembic_version is {current}; pass --force to overwrite"
                )
            conn.execute(
                text("UPDATE alembic_version SET version_num = :rev"),
                {"rev": args.revision},
            )
            print(f"alembic_version updated to {args.revision}")
            return
        conn.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:rev)"),
            {"rev": args.revision},
        )
        print(f"alembic_version stamped as {args.revision}")


if __name__ == "__main__":
    main()
