from app.config import get_settings
from app.trend_providers.common import TrendProviderResult


PROVIDER_NAME = "TikTok"


def collect_trends(region: str) -> TrendProviderResult:
    settings = get_settings()
    if not settings.tiktok_provider_enabled:
        return TrendProviderResult(
            provider_name=PROVIDER_NAME,
            status="unavailable",
            signals=[],
            note="TikTok Research access is not configured, so TruthLens does not claim TikTok trend coverage here.",
        )

    return TrendProviderResult(
        provider_name=PROVIDER_NAME,
        status="unavailable",
        signals=[],
        note="TikTok Research access is configured but no approved production trend profile is enabled in this environment.",
    )
