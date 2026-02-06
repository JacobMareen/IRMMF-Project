from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, Dict, Any

class SSOLoginResponse(BaseModel):
    """Return URL to redirect user to."""
    redirect_url: str

class SSOProfile(BaseModel):
    """Normalized user profile from any provider."""
    email: EmailStr
    provider: str
    provider_user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tenant_id: Optional[str] = None  # If provider supports multi-tenancy
    raw_attributes: Dict[str, Any] = {} # Backup of raw claim data

class SSOCallbackResponse(BaseModel):
    """Return JWT after successful exchange."""
    access_token: str
    token_type: str = "bearer"
