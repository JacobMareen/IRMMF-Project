from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App Info
    APP_TITLE: str = "IRMMF Command Center"
    APP_VERSION: str = "6.1-Alpha"
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg://localhost:5432/irmmf_db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_SSL_REQUIRED: bool = False  # Set to True in Production
    
    # Security
    DEBUG: bool = True  # Enable debug routes
    CORS_ALLOW_ALL: bool = False # If True, allow ["*"]; otherwise restricted.
    DEV_RBAC_DISABLED: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MAX_USERS_PER_TENANT: int = 5
    
    # Rate Limiting
    IRMMF_RATE_LIMIT_ENABLED: bool = True
    IRMMF_RATE_LIMIT_PER_MINUTE: int = 100
    IRMMF_RATE_LIMIT_WINDOW_SECONDS: int = 60
    IRMMF_MAX_BODY_MB: int = 10
    
    # Ingestion
    IRMMF_EXCEL_FILE: str = "IRMMF_QuestionBank_v10_StreamlinedIntake_20260117.xlsx"
    TRUNCATE_BANK: bool = False
    QUESTION_BANK_VERSION: Optional[str] = None
    
    # Analysis & Risk
    RISK_CONFIG_PATH: str = "config/risk_scenarios_simple.yaml"

    # AI Report Branding
    AI_REPORT_LOGO_PATH: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
