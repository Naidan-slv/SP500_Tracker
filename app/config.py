import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str


settings = Settings(
    database_url=os.getenv("DATABASE_URL", ""),
)

if not settings.database_url:
    raise RuntimeError("DATABASE_URL is not set. Add it to your .env file.")
