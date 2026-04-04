from app.config import get_settings
from app.trend_providers.common import TrendProviderResult


PROVIDER_NAME = "Instagram"


def collect_trends(region: str) -> TrendProviderResult:
    settings = get_settings()
    if not settings.instagram_provider_enabled:
        return TrendProviderResult(
            provider_name=PROVIDER_NAME,
            status="unavailable",
            signals=[],
            note="Broad Instagram trend access is not configured. TruthLens falls back to other providers instead of faking platform-wide trends.",
        )

    return TrendProviderResult(
        provider_name=PROVIDER_NAME,
        status="unavailable",
        signals=[],
        note="Instagram official access does not provide a safe general trend feed for this deployment profile, so the provider stays disabled.",
    )
