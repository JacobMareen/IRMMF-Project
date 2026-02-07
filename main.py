"""FastAPI entrypoint: routing + startup wiring for IRMMF services."""
from __future__ import annotations
import logging
import time
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth import resolve_principal_from_headers
from app import models
from app.core.bootstrap import register_modules, init_database
from app.core.config import allowed_origins
from app.db import get_db
from app.modules.assessment import service as services_module
from app.modules.assessment.routes import router as assessment_router
from app.modules.ai.routes import router as ai_router
from app.modules.dwf.routes import router as dwf_router
from app.modules.pia.routes import router as pia_router
from app.modules.tenant.routes import router as tenant_router
from app.modules.users.routes import router as users_router
from app.modules.cases.routes import router as cases_router
from app.modules.insider_program.routes import router as insider_program_router
from app.modules.insider_program.routes import router as insider_program_router
from app.modules.third_party.routes import router as third_party_router
from app.security.audit import AuditContext, reset_audit_context, set_audit_context
from app.security.rate_limit import RateLimiter, load_rate_limit_config, resolve_client_ip
from app.security import slowapi

from contextlib import asynccontextmanager
from app.core.settings import settings

logger = logging.getLogger(__name__)
START_TIME = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_database()
    if not settings.DEBUG and settings.SECRET_KEY == "dev-secret-key-change-in-prod":
        logger.warning(
            "SECRET_KEY is set to the default dev value. Set a secure SECRET_KEY in production."
        )
    yield
    # Shutdown (if needed)

# 2. Setup FastAPI App
app = FastAPI(title=settings.APP_TITLE, version=settings.APP_VERSION, lifespan=lifespan)

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


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)

rate_limit_config = load_rate_limit_config()
rate_limiter = RateLimiter(
    limit=rate_limit_config.limit_per_minute,
    window_seconds=rate_limit_config.window_seconds,
)
USE_SLOWAPI = slowapi.slowapi_enabled()

if USE_SLOWAPI and slowapi.limiter:
    app.state.limiter = slowapi.limiter
    app.add_exception_handler(
        slowapi.RateLimitExceeded,
        slowapi._rate_limit_exceeded_handler,
    )
    app.add_middleware(slowapi.SlowAPIMiddleware)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not rate_limit_config.enabled:
            return await call_next(request)
        if request.method in {"OPTIONS", "HEAD"}:
            return await call_next(request)
        content_length = request.headers.get("content-length")
        if content_length and rate_limit_config.max_body_bytes:
            try:
                if int(content_length) > rate_limit_config.max_body_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Payload too large."},
                    )
            except ValueError:
                pass
        if USE_SLOWAPI:
            return await call_next(request)
        client_ip = resolve_client_ip(request)
        allowed, retry_after = rate_limiter.allow(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please retry later."},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)


app.add_middleware(RateLimitMiddleware)


class PrincipalContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        principal = resolve_principal_from_headers(request.headers, allow_anonymous=True)
        if principal is not None:
            request.state.principal = principal
        forwarded = request.headers.get("x-forwarded-for") or request.headers.get("x-real-ip")
        client_ip = None
        if forwarded:
            client_ip = forwarded.split(",", 1)[0].strip()
        elif request.client:
            client_ip = request.client.host
        token = set_audit_context(
            AuditContext(
                actor=getattr(principal, "subject", None) if principal else None,
                ip_address=client_ip,
                user_agent=request.headers.get("user-agent"),
            )
        )
        try:
            return await call_next(request)
        finally:
            reset_audit_context(token)


app.add_middleware(PrincipalContextMiddleware)

# 3. Register module routers
app.include_router(assessment_router)
app.include_router(ai_router)
app.include_router(dwf_router)
app.include_router(pia_router)
app.include_router(tenant_router)
app.include_router(users_router)
app.include_router(cases_router)
app.include_router(insider_program_router)
app.include_router(third_party_router)
from app.modules.sso.routes import router as sso_router
app.include_router(sso_router)
from app.modules.research.routes import router as research_router
app.include_router(research_router)
from app.modules.content_library.routes import router as content_library_router
app.include_router(content_library_router)


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

@app.get("/api/v1/status")
def system_status(db: Session = Depends(get_db)):
    timestamp = datetime.now(timezone.utc).isoformat()
    uptime_s = int(time.time() - START_TIME)

    db_status = {"ok": True, "error": None, "latency_ms": None}
    qbank_status: dict = {}
    migration_status: dict = {}

    try:
        start = time.perf_counter()
        db.execute(text("SELECT 1")).scalar()
        db_status["latency_ms"] = int((time.perf_counter() - start) * 1000)
    except Exception as exc:
        db_status["ok"] = False
        db_status["error"] = str(exc)

    if db_status["ok"]:
        try:
            qbank_status = {
                "questions": db.execute(text("SELECT COUNT(*) FROM dim_questions")).scalar(),
                "answers": db.execute(text("SELECT COUNT(*) FROM dim_answers")).scalar(),
                "intake_responses": db.execute(text("SELECT COUNT(*) FROM fact_intake_responses")).scalar(),
            }
        except Exception as exc:
            qbank_status = {"error": str(exc)}

        try:
            latest_bank = db.execute(
                text(
                    """
                    SELECT version, source_file, source_sha256, created_at
                    FROM question_banks
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                )
            ).mappings().first()
            if latest_bank:
                qbank_status["latest"] = dict(latest_bank)
        except Exception as exc:
            qbank_status.setdefault("error", str(exc))

        try:
            migration_version = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
            migration_status = {"alembic_version": migration_version}
        except Exception as exc:
            migration_status = {"error": str(exc)}

    overall = "ok" if db_status["ok"] else "degraded"

    return {
        "status": overall,
        "timestamp": timestamp,
        "uptime_s": uptime_s,
        "app": {
            "title": settings.APP_TITLE,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
            "rbac_disabled": settings.DEV_RBAC_DISABLED,
            "rate_limit_enabled": settings.IRMMF_RATE_LIMIT_ENABLED,
        },
        "database": db_status,
        "question_bank": qbank_status,
        "migrations": migration_status,
    }


if settings.DEBUG:
    @app.get("/api/v1/debug/intake_counts")
    def debug_intake_counts(db: Session = Depends(get_db)):
        counts = {
            "dim_questions": db.execute(text("SELECT COUNT(*) FROM dim_questions")).scalar(),
            "dim_answers": db.execute(text("SELECT COUNT(*) FROM dim_answers")).scalar(),
            "fact_intake_responses": db.execute(text("SELECT COUNT(*) FROM fact_intake_responses")).scalar(),
        }
        sample = db.execute(
            text(
                """
                SELECT q_id, domain, question_text
                FROM dim_questions
                ORDER BY q_id
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
