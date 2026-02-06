from __future__ import annotations

from datetime import datetime, timezone
import os

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.modules.tenant import models as tenant_models
from app.modules.users import models
from app.core.settings import settings
from app.modules.tenant import models as tenant_models
from app.modules.users import models
from app.modules.users.schemas import LoginResponse, UserInviteIn, UserOut, TermsStatus
from app.security.jwt import create_access_token


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self._legacy_users_schema: bool | None = None
        self._has_user_roles_table: bool | None = None

    def list_users(self, tenant_key: str) -> list[UserOut]:
        if self._uses_legacy_users():
            return self._list_users_legacy(tenant_key)
        tenant = self._get_or_create_tenant(tenant_key)
        users = (
            self.db.query(models.User)
            .filter(models.User.tenant_id == tenant.id)
            .order_by(models.User.created_at.desc())
            .all()
        )
        return [self._serialize_user(user, include_roles=self._has_user_roles()) for user in users]

    def invite_user(self, tenant_key: str, payload: UserInviteIn) -> UserOut:
        if self._uses_legacy_users():
            return self._invite_user_legacy(tenant_key, payload)
        tenant = self._get_or_create_tenant(tenant_key)
        existing = (
            self.db.query(models.User)
            .filter(models.User.tenant_id == tenant.id)
            .filter(models.User.email == payload.email)
            .first()
        )
        if existing:
            raise ValueError("User already exists")

        # Enforce Account Limits (DDoS / Abuse Prevention)
        current_count = self.db.query(models.User).filter(models.User.tenant_id == tenant.id).count()
        if current_count >= settings.MAX_USERS_PER_TENANT:
            raise ValueError(f"Tenant has reached the maximum of {settings.MAX_USERS_PER_TENANT} users.")

        user = models.User(
            tenant_id=tenant.id,
            email=payload.email,
            display_name=payload.display_name,
            status="invited",
            invited_at=datetime.now(timezone.utc),
        )
        self.db.add(user)
        self.db.flush()
        role = models.UserRole(user_id=user.id, role=payload.role)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(user)
        return self._serialize_user(user)

    def login(self, tenant_key: str, email: str) -> LoginResponse:
        if self._uses_legacy_users():
            return self._login_legacy(tenant_key, email)
        tenant = self._get_or_create_tenant(tenant_key)
        user = (
            self.db.query(models.User)
            .filter(models.User.tenant_id == tenant.id)
            .filter(models.User.email == email)
            .first()
        )
        if not user:
            raise ValueError("User not found")
        user.status = "active"
        user.last_login_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        
        # Generate JWT
        token_payload = {
            "sub": str(user.id),
            "tenant_key": tenant_key,
            "roles": [r.role for r in user.roles] if self._has_user_roles() else ["TENANT_ADMIN"] # Fallback for legacy
        }
        token = create_access_token(token_payload)
        
        # Legacy dev fallback if configured and needed, but we prefer JWT now
        # token = os.getenv("DEV_TOKEN", "dev-token") 
        return LoginResponse(user=self._serialize_user(user, include_roles=self._has_user_roles()), token=token)

    def lookup_tenants(self, email: str) -> list[dict[str, str]]:
        if self._uses_legacy_users():
            return []

        results = (
            self.db.query(tenant_models.Tenant)
            .join(models.User, models.User.tenant_id == tenant_models.Tenant.id)
            .filter(models.User.email == email)
            .all()
        )

        return [
            {"name": t.tenant_name, "key": t.tenant_key}
            for t in results
        ]

    def get_terms_status(self, user_id: str, current_version: str = "1.0") -> TermsStatus:
        acceptance = (
            self.db.query(models.TermsAcceptance)
            .filter(
                models.TermsAcceptance.user_id == user_id,
                models.TermsAcceptance.terms_version == current_version
            )
            .first()
        )
        return TermsStatus(
            latest_version=current_version,
            has_accepted=bool(acceptance),
            accepted_at=acceptance.accepted_at if acceptance else None,
            required=True
        )

    def accept_terms(self, user_id: str, version: str, ip_address: str | None = None, user_agent: str | None = None) -> None:
        # Idempotent: check if already accepted
        existing = (
            self.db.query(models.TermsAcceptance)
            .filter(
                models.TermsAcceptance.user_id == user_id,
                models.TermsAcceptance.terms_version == version
            )
            .first()
        )
        if existing:
            return

        acceptance = models.TermsAcceptance(
            user_id=user_id,
            terms_version=version,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(acceptance)
        self.db.commit()

    def update_roles(self, tenant_key: str, user_id: str, roles: list[str]) -> UserOut:
        if self._uses_legacy_users():
            return self._update_roles_legacy(tenant_key, user_id, roles)
        tenant = self._get_or_create_tenant(tenant_key)
        user = (
            self.db.query(models.User)
            .filter(models.User.tenant_id == tenant.id)
            .filter(models.User.id == user_id)
            .first()
        )
        if not user:
            raise ValueError("User not found")
        # Replace roles
        self.db.query(models.UserRole).filter(models.UserRole.user_id == user.id).delete(synchronize_session=False)
        for role in roles:
            self.db.add(models.UserRole(user_id=user.id, role=role))
        self.db.commit()
        self.db.refresh(user)
        return self._serialize_user(user)

    def _get_or_create_tenant(self, tenant_key: str) -> tenant_models.Tenant:
        tenant = (
            self.db.query(tenant_models.Tenant)
            .filter(tenant_models.Tenant.tenant_key == tenant_key)
            .first()
        )
        if tenant:
            return tenant
        tenant = tenant_models.Tenant(
            tenant_key=tenant_key,
            tenant_name="Default Tenant" if tenant_key == "default" else tenant_key,
            environment_type="Production",
        )
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def _serialize_user(self, user: models.User, include_roles: bool = True) -> UserOut:
        roles = []
        if include_roles and self._has_user_roles():
            roles = user.roles or []
        return UserOut(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            status=user.status,
            marketing_consent=bool(getattr(user, "marketing_consent", False)),
            marketing_consent_at=getattr(user, "marketing_consent_at", None),
            roles=[{"role": role.role} for role in roles],
            invited_at=user.invited_at,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )

    def _table_columns(self, table_name: str) -> set[str]:
        rows = self.db.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :table_name
                """
            ),
            {"table_name": table_name},
        ).fetchall()
        return {row[0] for row in rows}

    def _has_table(self, table_name: str) -> bool:
        return bool(
            self.db.execute(
                text(
                    """
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = :table_name
                    LIMIT 1
                    """
                ),
                {"table_name": table_name},
            ).scalar()
        )

    def _uses_legacy_users(self) -> bool:
        if self._legacy_users_schema is None:
            columns = self._table_columns("users")
            self._legacy_users_schema = "user_id" in columns and "id" not in columns
        return self._legacy_users_schema

    def _has_user_roles(self) -> bool:
        if self._has_user_roles_table is None:
            self._has_user_roles_table = self._has_table("user_roles")
        return self._has_user_roles_table

    def _list_users_legacy(self, tenant_key: str) -> list[UserOut]:
        rows = self.db.execute(
            text(
                """
                SELECT u.user_id,
                       u.email,
                       u.display_name,
                       u.is_admin,
                       u.created_at,
                       o.org_key
                FROM users u
                LEFT JOIN orgs o ON o.org_id = u.org_id
                WHERE (CAST(:tenant_key AS TEXT) IS NULL OR o.org_key = CAST(:tenant_key AS TEXT))
                ORDER BY u.created_at DESC
                """
            ),
            {"tenant_key": tenant_key},
        ).mappings().all()
        results: list[UserOut] = []
        for row in rows:
            roles = [{"role": "TENANT_ADMIN"}] if row.get("is_admin") else [{"role": "VIEWER"}]
            created_at = row.get("created_at")
            results.append(
                UserOut(
                    id=str(row.get("user_id")),
                    email=row.get("email"),
                    display_name=row.get("display_name"),
                    status="active",
                    roles=roles,
                    invited_at=created_at,
                    last_login_at=None,
                    created_at=created_at,
                )
            )
        return results

    def _ensure_legacy_org(self, tenant_key: str) -> str:
        org_id = self.db.execute(
            text("SELECT org_id FROM orgs WHERE org_key = :key"),
            {"key": tenant_key},
        ).scalar()
        if org_id:
            return str(org_id)
        org_name = "Default Org" if tenant_key == "default" else tenant_key
        org_id = self.db.execute(
            text(
                "INSERT INTO orgs (name, org_key) VALUES (:name, :key) RETURNING org_id"
            ),
            {"name": org_name, "key": tenant_key},
        ).scalar()
        self.db.commit()
        return str(org_id)

    def _invite_user_legacy(self, tenant_key: str, payload: UserInviteIn) -> UserOut:
        org_id = self._ensure_legacy_org(tenant_key)
        existing = self.db.execute(
            text("SELECT 1 FROM users WHERE org_id = :org_id AND email = :email"),
            {"org_id": org_id, "email": payload.email},
        ).scalar()
        if existing:
            raise ValueError("User already exists")
        is_admin = payload.role.upper() in {"ADMIN", "TENANT_ADMIN"}
        row = self.db.execute(
            text(
                """
                INSERT INTO users (org_id, email, display_name, is_admin)
                VALUES (:org_id, :email, :display_name, :is_admin)
                RETURNING user_id, created_at
                """
            ),
            {
                "org_id": org_id,
                "email": payload.email,
                "display_name": payload.display_name,
                "is_admin": is_admin,
            },
        ).mappings().first()
        self.db.commit()
        roles = [{"role": "TENANT_ADMIN"}] if is_admin else [{"role": "VIEWER"}]
        return UserOut(
            id=str(row.get("user_id")),
            email=payload.email,
            display_name=payload.display_name,
            status="invited",
            roles=roles,
            invited_at=row.get("created_at"),
            last_login_at=None,
            created_at=row.get("created_at"),
        )

    def _login_legacy(self, tenant_key: str, email: str) -> LoginResponse:
        row = self.db.execute(
            text(
                """
                SELECT u.user_id,
                       u.email,
                       u.display_name,
                       u.is_admin,
                       u.created_at,
                       o.org_key
                FROM users u
                LEFT JOIN orgs o ON o.org_id = u.org_id
                WHERE u.email = :email AND (CAST(:tenant_key AS TEXT) IS NULL OR o.org_key = CAST(:tenant_key AS TEXT))
                LIMIT 1
                """
            ),
            {"email": email, "tenant_key": tenant_key},
        ).mappings().first()
        if not row:
            raise ValueError("User not found")
        roles = [{"role": "TENANT_ADMIN"}] if row.get("is_admin") else [{"role": "VIEWER"}]
        user = UserOut(
            id=str(row.get("user_id")),
            email=row.get("email"),
            display_name=row.get("display_name"),
            status="active",
            roles=roles,
            invited_at=row.get("created_at"),
            last_login_at=None,
            created_at=row.get("created_at"),
        )
        token = os.getenv("DEV_TOKEN", "dev-token")
        return LoginResponse(user=user, token=token)

    def _update_roles_legacy(self, tenant_key: str, user_id: str, roles: list[str]) -> UserOut:
        is_admin = any(role.upper() in {"ADMIN", "TENANT_ADMIN"} for role in roles)
        row = self.db.execute(
            text(
                """
                UPDATE users
                SET is_admin = :is_admin
                WHERE user_id = :user_id
                RETURNING user_id, email, display_name, is_admin, created_at
                """
            ),
            {"is_admin": is_admin, "user_id": user_id},
        ).mappings().first()
        if not row:
            raise ValueError("User not found")
        self.db.commit()
        role_payload = [{"role": "TENANT_ADMIN"}] if row.get("is_admin") else [{"role": "VIEWER"}]
        return UserOut(
            id=str(row.get("user_id")),
            email=row.get("email"),
            display_name=row.get("display_name"),
            status="active",
            roles=role_payload,
            invited_at=row.get("created_at"),
            last_login_at=None,
            created_at=row.get("created_at"),
        )
