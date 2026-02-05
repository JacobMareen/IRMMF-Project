"""AI reporting endpoints (executive summaries, narrative outputs)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
import uuid

from auth import Principal, get_principal
from app.db import get_db
from app.modules.ai.schemas import (
    ExecutiveSummaryRequest,
    ExecutiveSummaryResponse,
    ExecutiveSummaryHistoryOut,
    ExecutiveSummaryPinIn,
)
from app.modules.ai.pdf import render_executive_summary_pdf
from app.modules.ai.docx import render_executive_summary_docx
from app.modules.ai.service import (
    ExecutiveSummaryService,
    render_summary_html,
    _history_row_to_out,
    _history_row_to_response,
)
from app.security.access import tenant_principal_required


router = APIRouter(dependencies=[Depends(tenant_principal_required)])


def get_ai_service(db: Session = Depends(get_db)) -> ExecutiveSummaryService:
    return ExecutiveSummaryService(db)


@router.post("/api/v1/ai/executive-summary", response_model=ExecutiveSummaryResponse)
def generate_executive_summary(
    payload: ExecutiveSummaryRequest,
    principal: Principal = Depends(get_principal),
    service: ExecutiveSummaryService = Depends(get_ai_service),
):
    tenant_key = principal.tenant_key or "default"
    return service.generate(payload, tenant_key)


@router.get("/api/v1/ai/executive-summary/{assessment_id}", response_model=ExecutiveSummaryResponse)
def get_executive_summary(
    assessment_id: str,
    principal: Principal = Depends(get_principal),
    service: ExecutiveSummaryService = Depends(get_ai_service),
):
    tenant_key = principal.tenant_key or "default"
    summary = service.get_cached_summary(tenant_key, assessment_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Executive summary not found.")
    return summary


@router.get(
    "/api/v1/ai/executive-summary/{assessment_id}/history",
    response_model=list[ExecutiveSummaryHistoryOut],
)
def list_executive_summary_history(
    assessment_id: str,
    principal: Principal = Depends(get_principal),
    service: ExecutiveSummaryService = Depends(get_ai_service),
):
    tenant_key = principal.tenant_key or "default"
    return service.list_history(tenant_key, assessment_id)


@router.post(
    "/api/v1/ai/executive-summary/{assessment_id}/pin",
    response_model=ExecutiveSummaryResponse,
)
def pin_executive_summary(
    assessment_id: str,
    payload: ExecutiveSummaryPinIn,
    principal: Principal = Depends(get_principal),
    service: ExecutiveSummaryService = Depends(get_ai_service),
):
    try:
        history_uuid = uuid.UUID(payload.history_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid history id.")
    tenant_key = principal.tenant_key or "default"
    try:
        return service.pin_history(tenant_key, assessment_id, history_uuid)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/api/v1/ai/executive-summary/{assessment_id}/pin")
def unpin_executive_summary(
    assessment_id: str,
    principal: Principal = Depends(get_principal),
    service: ExecutiveSummaryService = Depends(get_ai_service),
):
    tenant_key = principal.tenant_key or "default"
    try:
        service.unpin_history(tenant_key, assessment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "unpinned"}


@router.get(
    "/api/v1/ai/executive-summary/history/{history_id}",
    response_model=ExecutiveSummaryHistoryOut,
)
def get_executive_summary_history_item(
    history_id: str,
    principal: Principal = Depends(get_principal),
    service: ExecutiveSummaryService = Depends(get_ai_service),
):
    try:
        history_uuid = uuid.UUID(history_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid history id.")
    tenant_key = principal.tenant_key or "default"
    row = service.get_history_item(tenant_key, history_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Summary history not found.")
    return _history_row_to_out(row)


@router.get("/api/v1/ai/executive-summary/history/{history_id}/pdf")
def download_history_pdf(
    history_id: str,
    principal: Principal = Depends(get_principal),
    service: ExecutiveSummaryService = Depends(get_ai_service),
):
    try:
        history_uuid = uuid.UUID(history_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid history id.")
    tenant_key = principal.tenant_key or "default"
    row = service.get_history_item(tenant_key, history_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Summary history not found.")
    summary = _history_row_to_response(row)
    pdf_bytes = render_executive_summary_pdf(summary)
    filename = f"executive_summary_{row.assessment_id or 'assessment'}_{history_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'},
    )


@router.get("/api/v1/ai/executive-summary/history/{history_id}/docx")
def download_history_docx(
    history_id: str,
    principal: Principal = Depends(get_principal),
    service: ExecutiveSummaryService = Depends(get_ai_service),
):
    try:
        history_uuid = uuid.UUID(history_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid history id.")
    tenant_key = principal.tenant_key or "default"
    row = service.get_history_item(tenant_key, history_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Summary history not found.")
    summary = _history_row_to_response(row)
    docx_bytes = render_executive_summary_docx(summary)
    filename = f"executive_summary_{row.assessment_id or 'assessment'}_{history_id}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'},
    )


@router.get("/api/v1/ai/executive-summary/history/{history_id}/html")
def download_history_html(
    history_id: str,
    principal: Principal = Depends(get_principal),
    service: ExecutiveSummaryService = Depends(get_ai_service),
):
    try:
        history_uuid = uuid.UUID(history_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid history id.")
    tenant_key = principal.tenant_key or "default"
    row = service.get_history_item(tenant_key, history_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Summary history not found.")
    summary = _history_row_to_response(row)
    html = summary.summary_html or render_summary_html(summary)
    filename = f"executive_summary_{row.assessment_id or 'assessment'}_{history_id}.html"
    return Response(
        content=html,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'},
    )

@router.post("/api/v1/ai/executive-summary/pdf")
def generate_executive_summary_pdf(
    payload: ExecutiveSummaryRequest,
    principal: Principal = Depends(get_principal),
    service: ExecutiveSummaryService = Depends(get_ai_service),
):
    tenant_key = principal.tenant_key or "default"
    summary = service.generate(payload, tenant_key)
    pdf_bytes = render_executive_summary_pdf(summary)
    filename = f"executive_summary_{payload.assessment_id or 'assessment'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/api/v1/ai/executive-summary/docx")
def generate_executive_summary_docx(
    payload: ExecutiveSummaryRequest,
    principal: Principal = Depends(get_principal),
    service: ExecutiveSummaryService = Depends(get_ai_service),
):
    tenant_key = principal.tenant_key or "default"
    summary = service.generate(payload, tenant_key)
    docx_bytes = render_executive_summary_docx(summary)
    filename = f"executive_summary_{payload.assessment_id or 'assessment'}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
