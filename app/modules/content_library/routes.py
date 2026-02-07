from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.modules.content_library.service import PolicyGeneratorService
from auth import get_principal, Principal
from app.modules.tenant.models import TenantSettings


router = APIRouter(tags=["content-library"])

@router.get("/api/v1/content/policy/{policy_type}")
def download_policy(
    policy_type: str,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db)
):
    """
    Download a dynamically generated policy (Markdown).
    policy_type: 'aup' or 'itp'
    """
    # Fetch Tenant Details for personalization
    # Assuming simple lookup based on tenant_key from principal
    # In a real scenario, use a proper Service to fetch TenantSettings
    settings = db.query(TenantSettings).filter(
        TenantSettings.tenant.has(tenant_key=principal.tenant_key)
    ).first()
    
    company_name = settings.company_name if settings and settings.company_name else "My Organization"
    industry = settings.industry_sector if settings and settings.industry_sector else "General"

    service = PolicyGeneratorService()
    content = service.generate_policy(policy_type, company_name, industry)
    
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={policy_type.upper()}_Policy.md"}
    )

@router.get("/api/v1/content/templates", response_model=list[dict])
async def list_templates():
    """
    List all available templates in the content library.
    """
    from app.modules.content_library.service import TemplateService
    return TemplateService.list_templates()

@router.get("/api/v1/content/templates/{template_id}", response_model=dict)
async def get_template(template_id: str):
    """
    Get the content and metadata for a specific template.
    """
    from fastapi import HTTPException
    from app.modules.content_library.service import TemplateService
    
    template = TemplateService.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template
