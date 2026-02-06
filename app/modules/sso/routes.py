from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.modules.sso.schemas import SSOCallbackResponse
from app.modules.sso.service import SSOService

router = APIRouter()

def get_sso_service(db: Session = Depends(get_db)) -> SSOService:
    return SSOService(db)

@router.get("/api/v1/auth/sso/login/{provider_id}")
def sso_login(
    provider_id: str,
    redirect_uri: str = Query(..., description="Callback URI where IdP will post code"),
    service: SSOService = Depends(get_sso_service)
):
    """Start SSO flow - redirects user to IdP."""
    try:
        url = service.handle_login(provider_id, redirect_uri)
        return RedirectResponse(url)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/api/v1/auth/sso/callback/{provider_id}", response_model=SSOCallbackResponse)
def sso_callback(
    provider_id: str,
    code: str,
    redirect_uri: str,
    service: SSOService = Depends(get_sso_service)
):
    """Exchange code for token."""
    try:
        return service.process_callback(provider_id, code, redirect_uri)
    except Exception as e:
        # Security: Don't leak exact error details in prod, but helpful for alpha
        raise HTTPException(status_code=400, detail=f"SSO Failed: {str(e)}")
