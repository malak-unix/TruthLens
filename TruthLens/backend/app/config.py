import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
if not os.getenv("GEMINI_API_KEY"):
    load_dotenv(BASE_DIR / ".env.example")


def normalize_gemini_model(model_name: str) -> str:
    normalized = (model_name or "").strip()
    if normalized in {"", "gemini-1.5-flash", "gemini-1.5-flash-latest"}:
        return "gemini-2.0-flash"
    return normalized


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    gemini_timeout_seconds: int

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=normalize_gemini_model(os.getenv("GEMINI_MODEL", "gemini-2.0-flash")),
        gemini_timeout_seconds=int(os.getenv("GEMINI_TIMEOUT_SECONDS", "25")),
    )
