from app.config import get_settings
from app.trend_providers.common import TrendProviderResult


PROVIDER_NAME = "X"


def collect_trends(region: str) -> TrendProviderResult:
    settings = get_settings()
    if not settings.x_enabled:
        return TrendProviderResult(
            provider_name=PROVIDER_NAME,
            status="unavailable",
            signals=[],
            note="X trend search is disabled because no X_BEARER_TOKEN is configured.",
        )

    return TrendProviderResult(
        provider_name=PROVIDER_NAME,
        status="unavailable",
        signals=[],
        note="X integration is ready for configured official access, but no safe trend query profile is enabled in this environment.",
    )
