from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional, Dict, Any

MAX_URL_LEN = 2048
MAX_PROVIDER_LEN = 64
MAX_ID_LEN = 128
MAX_NAME_LEN = 120
MAX_TENANT_LEN = 120
MAX_TOKEN_LEN = 4096

class SSOLoginResponse(BaseModel):
    """Return URL to redirect user to."""
    redirect_url: str = Field(max_length=MAX_URL_LEN)

class SSOProfile(BaseModel):
    """Normalized user profile from any provider."""
    email: EmailStr
    provider: str = Field(max_length=MAX_PROVIDER_LEN)
    provider_user_id: str = Field(max_length=MAX_ID_LEN)
    first_name: Optional[str] = Field(default=None, max_length=MAX_NAME_LEN)
    last_name: Optional[str] = Field(default=None, max_length=MAX_NAME_LEN)
    tenant_id: Optional[str] = Field(default=None, max_length=MAX_TENANT_LEN)  # If provider supports multi-tenancy
    raw_attributes: Dict[str, Any] = {} # Backup of raw claim data

class SSOCallbackResponse(BaseModel):
    """Return JWT after successful exchange."""
    access_token: str = Field(max_length=MAX_TOKEN_LEN)
    token_type: str = Field(default="bearer", max_length=MAX_PROVIDER_LEN)
