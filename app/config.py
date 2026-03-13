import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    app_base_url: str
    frontend_base_url: str
    smtp_enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str
    smtp_use_tls: bool
    smtp_use_ssl: bool
    finnhub_api_key: str


settings = Settings(
    database_url=os.getenv("DATABASE_URL", ""),
    jwt_secret_key=os.getenv("JWT_SECRET_KEY", "dev-change-me-secret"),
    jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
    app_base_url=os.getenv("APP_BASE_URL", "http://localhost:8000"),
    frontend_base_url=os.getenv("FRONTEND_URL", "http://localhost:5174"),
    smtp_enabled=os.getenv("SMTP_ENABLED", "false").lower() == "true",
    smtp_host=os.getenv("SMTP_HOST", ""),
    smtp_port=int(os.getenv("SMTP_PORT", "587")),
    smtp_username=os.getenv("SMTP_USERNAME", ""),
    smtp_password=os.getenv("SMTP_PASSWORD", ""),
    smtp_from_email=os.getenv("SMTP_FROM_EMAIL", ""),
    smtp_from_name=os.getenv("SMTP_FROM_NAME", "SP500 Tracker"),
    smtp_use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
    smtp_use_ssl=os.getenv("SMTP_USE_SSL", "false").lower() == "true",
    finnhub_api_key=os.getenv("FINNHUB_API_KEY", ""),
)

if not settings.database_url:
    raise RuntimeError("DATABASE_URL is not set. Add it to your .env file.")
