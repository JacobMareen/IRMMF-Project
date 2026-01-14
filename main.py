"""FastAPI entrypoint: routing + startup wiring for IRMMF services."""
from __future__ import annotations
from fastapi import FastAPI, Depends
import os
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models
from app.core.bootstrap import register_modules, init_database
from app.core.config import allowed_origins
from app.db import get_db
from app.modules.assessment import service as services_module
from app.modules.assessment.routes import router as assessment_router
from app.modules.dwf.routes import router as dwf_router

# 1. Initialize Database Tables (safe to run on restart)
init_database()

# 2. Setup FastAPI App
app = FastAPI(title="IRMMF Command Center", version="6.1-Alpha")

# Central module registry (modules are peers).
module_registry = register_modules()

# CORS (Allow UI to talk to API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Register module routers
app.include_router(assessment_router)
app.include_router(dwf_router)


@app.get("/")
def health_check():
    return {
        "status": "IRMMF v6.1 Online",
        "mode": "Neuro-Adaptive",
        "modules": {k: vars(v) for k, v in module_registry.list_modules().items()},
    }


@app.get("/api/v1/modules")
def list_modules():
    return {k: vars(v) for k, v in module_registry.list_modules().items()}


@app.get("/api/v1/debug/intake_counts")
def debug_intake_counts(db: Session = Depends(get_db)):
    counts = {
        "dim_intake_questions": db.execute(text("SELECT COUNT(*) FROM dim_intake_questions")).scalar(),
        "dim_intake_list_options": db.execute(text("SELECT COUNT(*) FROM dim_intake_list_options")).scalar(),
    }
    sample = db.execute(
        text(
            """
            SELECT intake_q_id, section, question_text
            FROM dim_intake_questions
            ORDER BY intake_q_id
            LIMIT 1
            """
        )
    ).mappings().first()
    counts["sample_question"] = sample
    counts["services_file"] = services_module.__file__
    counts["intake_fn_line"] = services_module.AssessmentService.get_intake_questions.__code__.co_firstlineno
    service_payload = services_module.AssessmentService(db).get_intake_questions()
    counts["service_payload_len"] = len(service_payload)
    counts["service_payload_sample"] = service_payload[:2]
    counts["intake_route_handlers"] = [
        route.name for route in app.routes if getattr(route, "path", None) == "/api/v1/intake/start"
    ]
    return counts
