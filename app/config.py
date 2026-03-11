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
    email_verification_token_expire_hours: int
    expose_verification_token: bool
    app_base_url: str


settings = Settings(
    database_url=os.getenv("DATABASE_URL", ""),
    jwt_secret_key=os.getenv("JWT_SECRET_KEY", "dev-change-me-secret"),
    jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
    email_verification_token_expire_hours=int(os.getenv("EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS", "24")),
    expose_verification_token=os.getenv("EXPOSE_VERIFICATION_TOKEN", "true").lower() == "true",
    app_base_url=os.getenv("APP_BASE_URL", "http://localhost:8000"),
)

if not settings.database_url:
    raise RuntimeError("DATABASE_URL is not set. Add it to your .env file.")
