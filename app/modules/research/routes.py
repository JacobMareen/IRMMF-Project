from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.modules.research.service import ResearchService
from app.security.rbac import require_roles

router = APIRouter(tags=["research"])

@router.get("/api/v1/research/export")
def export_research_data(
    db: Session = Depends(get_db),
    # Require ADMIN role. In future, restrict to SUPER_ADMIN.
    principal = Depends(require_roles("ADMIN"))
):
    """
    Download anonymized market research data as CSV.
    Requires ADMIN role.
    """
    service = ResearchService(db)
    
    return StreamingResponse(
        service.get_export_stream(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=market_research_export.csv"}
    )
