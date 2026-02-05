from __future__ import annotations

from sqlalchemy.orm import Session

from datetime import datetime

from app.modules.tenant import models
from app.modules.tenant.schemas import (
    TenantHolidayCreate,
    TenantHolidayOut,
    TenantSettingsIn,
    TenantSettingsOut,
    RegistrationRequest,
    RegistrationResponse,
)


class TenantService:
    def __init__(self, db: Session):
        self.db = db

    def get_settings(self, tenant_key: str) -> TenantSettingsOut:
        tenant = self._get_or_create_tenant(tenant_key)
        settings = tenant.settings
        if not settings:
            settings = models.TenantSettings(
                tenant_id=tenant.id,
                company_name="TBD Company",
                default_jurisdiction="Belgium",
                investigation_mode="standard",
                retention_days=365,
                keyword_flagging_enabled=False,
                keyword_list=[],
                weekend_days=[5, 6],
                saturday_is_business_day=False,
                deadline_cutoff_hour=17,
                notifications_enabled=True,
                serious_cause_notifications_enabled=True,
                jurisdiction_rules=models._default_jurisdiction_rules(),
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(tenant)
            self.db.refresh(settings)
        return self._serialize_settings(tenant, settings)

    def update_settings(self, tenant_key: str, payload: TenantSettingsIn) -> TenantSettingsOut:
        tenant = self._get_or_create_tenant(tenant_key)
        settings = tenant.settings
        if not settings:
            settings = models.TenantSettings(tenant_id=tenant.id)
            self.db.add(settings)

        data = payload.model_dump(exclude_unset=True)
        tenant_name = data.pop("tenant_name", None)
        environment_type = data.pop("environment_type", None)
        if tenant_name:
            tenant.tenant_name = tenant_name
        if environment_type:
            tenant.environment_type = environment_type

        for key, value in data.items():
            setattr(settings, key, value)

        self.db.commit()
        self.db.refresh(tenant)
        self.db.refresh(settings)
        return self._serialize_settings(tenant, settings)

    def _get_or_create_tenant(self, tenant_key: str) -> models.Tenant:
        tenant = (
            self.db.query(models.Tenant)
            .filter(models.Tenant.tenant_key == tenant_key)
            .first()
        )
        if tenant:
            return tenant
        tenant = models.Tenant(
            tenant_key=tenant_key,
            tenant_name="Default Tenant" if tenant_key == "default" else tenant_key,
            environment_type="Production",
        )
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def _serialize_settings(self, tenant: models.Tenant, settings: models.TenantSettings) -> TenantSettingsOut:
        return TenantSettingsOut(
            tenant_key=tenant.tenant_key,
            tenant_name=tenant.tenant_name,
            environment_type=tenant.environment_type,
            company_name=settings.company_name,
            default_jurisdiction=settings.default_jurisdiction,
            investigation_mode=settings.investigation_mode,
            retention_days=settings.retention_days,
            keyword_flagging_enabled=settings.keyword_flagging_enabled,
            keyword_list=settings.keyword_list or [],
            weekend_days=settings.weekend_days or [5, 6],
            saturday_is_business_day=settings.saturday_is_business_day,
            deadline_cutoff_hour=settings.deadline_cutoff_hour,
            notifications_enabled=settings.notifications_enabled,
            serious_cause_notifications_enabled=settings.serious_cause_notifications_enabled,
            jurisdiction_rules=settings.jurisdiction_rules or {},
            updated_at=settings.updated_at,
        )

    def list_holidays(self, tenant_key: str) -> list[TenantHolidayOut]:
        tenant = self._get_or_create_tenant(tenant_key)
        holidays = (
            self.db.query(models.TenantHoliday)
            .filter(models.TenantHoliday.tenant_id == tenant.id)
            .order_by(models.TenantHoliday.holiday_date.asc())
            .all()
        )
        return [
            TenantHolidayOut(
                id=item.id,
                holiday_date=item.holiday_date.isoformat(),
                label=item.label,
                created_at=item.created_at,
            )
            for item in holidays
        ]

    def add_holiday(self, tenant_key: str, payload: TenantHolidayCreate) -> TenantHolidayOut:
        tenant = self._get_or_create_tenant(tenant_key)
        holiday_date = datetime.fromisoformat(payload.holiday_date).date()
        holiday = models.TenantHoliday(
            tenant_id=tenant.id,
            holiday_date=holiday_date,
            label=payload.label,
        )
        self.db.add(holiday)
        self.db.commit()
        self.db.refresh(holiday)
        return TenantHolidayOut(
            id=holiday.id,
            holiday_date=holiday.holiday_date.isoformat(),
            label=holiday.label,
            created_at=holiday.created_at,
        )

    def delete_holiday(self, tenant_key: str, holiday_id: int) -> None:
        tenant = self._get_or_create_tenant(tenant_key)
        self.db.query(models.TenantHoliday).filter(
            models.TenantHoliday.tenant_id == tenant.id,
            models.TenantHoliday.id == holiday_id,
        ).delete()
        self.db.commit()
    def register_tenant(self, payload: RegistrationRequest) -> RegistrationResponse:
        # 1. Generate unique tenant_key
        base_key = payload.company_name.lower().replace(" ", "-").replace("'", "").replace(".", "")
        # Remove non-alphanumeric chars
        base_key = "".join(c for c in base_key if c.isalnum() or c == "-")
        
        # Check uniqueness
        existing = self.db.query(models.Tenant).filter(models.Tenant.tenant_key == base_key).first()
        if existing:
            # Simple suffix logic
            import random
            base_key = f"{base_key}-{random.randint(100, 999)}"
        
        tenant_key = base_key

        # 2. Check if email already exists globally (optional, but good practice)
        from app.modules.users.models import User, UserRole
        existing_user = self.db.query(User).filter(User.email == payload.admin_email).first()
        if existing_user:
            raise ValueError(f"User with email {payload.admin_email} already exists.")

        try:
            # 3. Create Tenant
            tenant = models.Tenant(
                tenant_key=tenant_key,
                tenant_name=payload.company_name,
                environment_type=payload.environment_type or "Production",
            )
            self.db.add(tenant)
            self.db.flush() # Get ID

            # 4. Create Settings Default
            settings = models.TenantSettings(
                tenant_id=tenant.id,
                company_name=payload.company_name,
                notifications_enabled=True
            )
            self.db.add(settings)

            # 5. Create Admin User
            user = User(
                tenant_id=tenant.id,
                email=payload.admin_email,
                display_name=payload.admin_name,
                status="active", # Auto-activate for now
                invited_at=datetime.now(),
                last_login_at=None
            )
            self.db.add(user)
            self.db.flush()

            # 6. Assign Admin Role
            role = UserRole(user_id=user.id, role="ADMIN")
            self.db.add(role)

            self.db.commit()

            return RegistrationResponse(
                tenant_key=tenant_key,
                admin_email=payload.admin_email,
                status="success",
                message="Tenant created successfully.",
                login_url=f"/login?tenant={tenant_key}"
            )

        except Exception as e:
            self.db.rollback()
            raise e
