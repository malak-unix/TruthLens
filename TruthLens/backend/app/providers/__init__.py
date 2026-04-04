from . import gdelt_provider, gnews_provider, guardian_provider, newsapi_provider


GENERAL_FEED_PROVIDERS = (
    gnews_provider,
    newsapi_provider,
    guardian_provider,
)

PRIORITY_FEED_PROVIDERS = (
    gnews_provider,
    newsapi_provider,
    gdelt_provider,
    guardian_provider,
)

TREND_MONITOR_PROVIDERS = (
    gdelt_provider,
)
