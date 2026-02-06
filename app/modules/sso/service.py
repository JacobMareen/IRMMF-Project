from typing import Dict, Type
from sqlalchemy.orm import Session
from app.modules.sso.protocols import IdentityProvider
from app.modules.sso.schemas import SSOProfile, SSOCallbackResponse
from app.modules.users.service import UserService
# We will use the existing JWT utility
from app.security.jwt import create_access_token

class SSOService:
    _registry: Dict[str, IdentityProvider] = {}

    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)

    @classmethod
    def register_provider(cls, provider: IdentityProvider):
        """Register a provider implementation."""
        cls._registry[provider.provider_id] = provider

    def get_provider(self, provider_id: str) -> IdentityProvider:
        """Get provider by ID or raise error."""
        provider = self._registry.get(provider_id)
        if not provider:
            # Simple error for alpha
            raise ValueError(f"Provider '{provider_id}' not configured.")
        return provider

    def handle_login(self, provider_id: str, redirect_uri: str) -> str:
        """Get the external login URL."""
        provider = self.get_provider(provider_id)
        return provider.get_login_url(redirect_uri)

    def process_callback(self, provider_id: str, code: str, redirect_uri: str) -> SSOCallbackResponse:
        """Exchange code, sync user, issue JWT."""
        provider = self.get_provider(provider_id)
        profile = provider.handle_callback(code, redirect_uri)
        
        # Sync user to DB
        # TODO: Add logic to `UserService` to upsert by email + provider
        # For now, we assume email matching for prep.
        # This part requires expanding UserService later.
        user = self._sync_user(profile)
        
        # Issue JWT
        token = create_access_token(
            data={"sub": user.email, "roles": user.roles, "tenant_key": user.tenant_id}
        )
        return SSOCallbackResponse(access_token=token)

    def _sync_user(self, profile: SSOProfile):
        """Internal helper to upsert user."""
        # Mock implementation for scaffolding phase. 
        # Real implementation will need UserService.upsert_external_user(profile)
        # For now, let's just lookup by email to verify flow.
        existing = self.user_service.get_user_by_email(profile.email)
        if existing:
            return existing
        
        # If new user, create them (auto-provision or fail based on policy)
        # For now, we raise if not found to be safe in prep.
        raise ValueError(f"User {profile.email} not found. Auto-provisioning not yet enabled.")
