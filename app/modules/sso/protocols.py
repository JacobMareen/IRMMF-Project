from typing import Protocol, Dict, Any
from app.modules.sso.schemas import SSOProfile

class IdentityProvider(Protocol):
    """Interface that all SSO providers (Auth0, AzureAD, SAML) must implement."""
    
    @property
    def provider_id(self) -> str:
        """Unique ID, e.g. 'auth0', 'azure-ad'."""
        ...
        
    def get_login_url(self, redirect_uri: str, state: str | None = None) -> str:
        """Generate the redirect URL for the provider."""
        ...
        
    def handle_callback(self, code: str, redirect_uri: str) -> SSOProfile:
        """Exchange code for tokens and return normalized profile."""
        ...
