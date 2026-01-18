"""Central configuration helpers."""
from __future__ import annotations

import os
from typing import List


def allowed_origins() -> List[str]:
    local_origins = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
        "http://0.0.0.0:5500",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://127.0.0.1:5175",
        "http://localhost:5175",
        "null",
    ]
    allow_origins = os.getenv("IRMMF_ALLOWED_ORIGINS")
    if not allow_origins:
        return local_origins
    return [o.strip() for o in allow_origins.split(",") if o.strip()]
