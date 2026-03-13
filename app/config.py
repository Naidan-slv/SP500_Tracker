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
    finnhub_api_key: str


settings = Settings(
    database_url=os.getenv("DATABASE_URL", ""),
    jwt_secret_key=os.getenv("JWT_SECRET_KEY", "dev-change-me-secret"),
    jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
    app_base_url=os.getenv("APP_BASE_URL", "http://localhost:8000"),
    frontend_base_url=os.getenv("FRONTEND_URL", "http://localhost:5174"),
    finnhub_api_key=os.getenv("FINNHUB_API_KEY", ""),
)

if not settings.database_url:
    raise RuntimeError("DATABASE_URL is not set. Add it to your .env file.")
