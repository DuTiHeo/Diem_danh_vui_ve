from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEU Attendance System"
    VERSION: str = "1.0.0"

    # Database
    POSTGRES_USER: str = "neu_admin"
    POSTGRES_PASSWORD: str = "neu_password"
    POSTGRES_DB: str = "neu_attendance"
    DATABASE_URL: str = "postgresql+asyncpg://neu_admin:neu_password@localhost:5432/neu_attendance"

    # JWT Authentication
    JWT_SECRET: str = "supersecretkey_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Microsoft OAuth
    MICROSOFT_CLIENT_ID: str = "your_client_id"
    MICROSOFT_CLIENT_SECRET: str = "your_client_secret"
    MICROSOFT_TENANT_ID: str = "your_tenant_id"
    MICROSOFT_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/callback"

    # Feature Flags
    DEV_MOCK_AUTH: bool = True

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

