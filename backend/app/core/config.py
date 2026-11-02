from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "NEU Attendance - Multi-Layer Smart Classroom Attendance System"
    VERSION: str = "2.0.0"
    BACKEND_INSTANCE_ID: str = "backend-local"

    # Database (PostgreSQL 16)
    POSTGRES_USER: str = "neu_admin"
    POSTGRES_PASSWORD: str = "neu_password"
    POSTGRES_DB: str = "neu_attendance"
    DATABASE_URL: str = "postgresql+asyncpg://neu_admin:neu_password@localhost:5432/neu_attendance"

    # Connection Pool Settings (Chapter 6.1 SYSTEM_DESIGN.md)
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 10
    DB_POOL_RECYCLE: int = 1800

    # Redis 7 (Chapter 3 & 4 SYSTEM_DESIGN.md)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Network & Domain
    DOMAIN_OR_IP: str = "localhost"
    SERVER_LAN_IP: str = ""

    # JWT Authentication
    JWT_SECRET: str = "supersecretkey_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Microsoft OAuth
    MICROSOFT_CLIENT_ID: str = "your_client_id"
    MICROSOFT_CLIENT_SECRET: str = "your_client_secret"
    MICROSOFT_TENANT_ID: str = "your_tenant_id"
    MICROSOFT_REDIRECT_URI: str = "http://localhost/api/v1/auth/callback"

    # Feature Flags
    DEV_MOCK_AUTH: bool = True

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
