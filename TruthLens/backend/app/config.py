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
load_local_env_file(BASE_DIR / ".env.example")


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
    guardian_api_key: str
    gdelt_enabled: bool
    x_bearer_token: str
    reddit_enabled: bool
    reddit_user_agent: str
    instagram_access_token: str
    instagram_enabled: bool
    tiktok_research_access_token: str
    tiktok_enabled: bool

    request_timeout_seconds: int
    rss_timeout_seconds: int
    default_refresh_limit: int
    general_feed_limit: int
    priority_feed_limit: int
    gdelt_max_records: int
    refresh_interval_minutes: int
    startup_refresh_max_age_minutes: int
    social_trend_limit: int
    trend_provider_timeout_seconds: int
    enable_og_image_fallback: bool
    image_metadata_timeout_seconds: int
    news_history_retention_days: int

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key.strip())

    @property
    def newsapi_enabled(self) -> bool:
        return bool(self.newsapi_api_key.strip())

    @property
    def gnews_enabled(self) -> bool:
        return bool(self.gnews_api_key.strip())

    @property
    def guardian_enabled(self) -> bool:
        return bool((self.guardian_api_key or "").strip())

    @property
    def x_enabled(self) -> bool:
        return bool(self.x_bearer_token.strip())

    @property
    def instagram_provider_enabled(self) -> bool:
        return self.instagram_enabled and bool(self.instagram_access_token.strip())

    @property
    def tiktok_provider_enabled(self) -> bool:
        return self.tiktok_enabled and bool(self.tiktok_research_access_token.strip())


@lru_cache
def get_settings() -> Settings:
    default_refresh_limit = int(os.getenv("DEFAULT_REFRESH_LIMIT", "12"))

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
        guardian_api_key=os.getenv("GUARDIAN_API_KEY", ""),
        gdelt_enabled=os.getenv("ENABLE_GDELT", "true").lower() == "true",
        x_bearer_token=os.getenv("X_BEARER_TOKEN", ""),
        reddit_enabled=os.getenv("ENABLE_REDDIT_TRENDS", "true").lower() == "true",
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "TruthLens/1.0"),
        instagram_access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN", ""),
        instagram_enabled=os.getenv("ENABLE_INSTAGRAM_TRENDS", "false").lower() == "true",
        tiktok_research_access_token=os.getenv("TIKTOK_RESEARCH_ACCESS_TOKEN", ""),
        tiktok_enabled=os.getenv("ENABLE_TIKTOK_TRENDS", "false").lower() == "true",

        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "8")),
        rss_timeout_seconds=int(os.getenv("RSS_TIMEOUT_SECONDS", "6")),
        default_refresh_limit=default_refresh_limit,
        general_feed_limit=int(os.getenv("GENERAL_FEED_LIMIT", str(default_refresh_limit))),
        priority_feed_limit=int(os.getenv("PRIORITY_FEED_LIMIT", "6")),
        gdelt_max_records=int(os.getenv("GDELT_MAX_RECORDS", "10")),
        refresh_interval_minutes=int(os.getenv("REFRESH_INTERVAL_MINUTES", "45")),
        startup_refresh_max_age_minutes=int(os.getenv("STARTUP_REFRESH_MAX_AGE_MINUTES", "120")),
        social_trend_limit=int(os.getenv("SOCIAL_TREND_LIMIT", "8")),
        trend_provider_timeout_seconds=int(os.getenv("TREND_PROVIDER_TIMEOUT_SECONDS", "8")),
        enable_og_image_fallback=os.getenv("ENABLE_OG_IMAGE_FALLBACK", "true").lower() == "true",
        image_metadata_timeout_seconds=int(os.getenv("IMAGE_METADATA_TIMEOUT_SECONDS", "5")),
        news_history_retention_days=int(os.getenv("NEWS_HISTORY_RETENTION_DAYS", "365")),
    )
