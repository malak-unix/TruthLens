import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def load_local_env_file(path: Path):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


load_local_env_file(BASE_DIR / ".env")


def normalize_gemini_model(model_name: str) -> str:
    normalized = (model_name or "").strip()
    return normalized or "gemini-2.5-flash"


@dataclass(frozen=True)
class Settings:
    app_env: str
    debug: bool
    enable_debug_endpoints: bool

    gemini_api_key: str
    gemini_model: str
    gemini_timeout_seconds: int

    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_hours: int

    newsapi_api_key: str
    gnews_api_key: str

    request_timeout_seconds: int
    rss_timeout_seconds: int
    default_refresh_limit: int

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key.strip())

    @property
    def newsapi_enabled(self) -> bool:
        return bool(self.newsapi_api_key.strip())

    @property
    def gnews_enabled(self) -> bool:
        return bool(self.gnews_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        debug=os.getenv("DEBUG", "true").lower() == "true",
        enable_debug_endpoints=os.getenv("ENABLE_DEBUG_ENDPOINTS", "true").lower() == "true",

        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=normalize_gemini_model(os.getenv("GEMINI_MODEL", "gemini-2.5-flash")),
        gemini_timeout_seconds=int(os.getenv("GEMINI_TIMEOUT_SECONDS", "25")),

        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "change-this-truthlens-secret"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_access_token_expire_hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_HOURS", "24")),

        newsapi_api_key=os.getenv("NEWSAPI_API_KEY", ""),
        gnews_api_key=os.getenv("GNEWS_API_KEY", ""),

        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "8")),
        rss_timeout_seconds=int(os.getenv("RSS_TIMEOUT_SECONDS", "6")),
        default_refresh_limit=int(os.getenv("DEFAULT_REFRESH_LIMIT", "12")),
    )