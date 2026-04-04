from app.config import get_settings
from app.priority_topics import MOROCCO_SCOPE_TERMS
from app.providers.common import FetchRequest, normalize_article, request_json


PROVIDER_NAME = "GNews"
BASE_URL = "https://gnews.io/api/v4"


def fetch_general(request: FetchRequest) -> list[dict]:
    settings = get_settings()
    if not settings.gnews_enabled:
        return []

    params = {
        "token": settings.gnews_api_key,
        "lang": "en",
        "max": request.limit,
    }

    if request.region == "ma":
        params["country"] = "ma"
        params["category"] = "general"
    else:
        params["topic"] = "world"

    data = request_json(
        f"{BASE_URL}/top-headlines",
        params=params,
        timeout=settings.request_timeout_seconds,
    )
    if not data:
        return []

    return _normalize_articles(data.get("articles", []), request)


def fetch_priority(request: FetchRequest) -> list[dict]:
    settings = get_settings()
    if not settings.gnews_enabled or not request.topic_bundle:
        return []

    query_terms = list(request.topic_bundle.keywords[:4])
    if request.region == "ma":
        scope_terms = request.topic_bundle.region_scope_terms or MOROCCO_SCOPE_TERMS
        query_terms = [*scope_terms[:3], *query_terms]

    params = {
        "token": settings.gnews_api_key,
        "lang": "en",
        "max": request.limit,
        "sortby": "publishedAt",
        "q": " ".join(query_terms[:7]),
    }

    if request.region == "ma":
        params["country"] = "ma"

    data = request_json(
        f"{BASE_URL}/search",
        params=params,
        timeout=settings.request_timeout_seconds,
    )
    if not data:
        return []

    return _normalize_articles(data.get("articles", []), request)


def _normalize_articles(raw_articles: list[dict], request: FetchRequest) -> list[dict]:
    results = []

    for article in raw_articles:
        item = normalize_article(
            provider_name=PROVIDER_NAME,
            title=article.get("title") or "",
            description=article.get("description") or "",
            url=article.get("url") or "",
            published_at=article.get("publishedAt") or "",
            source_name=(article.get("source") or {}).get("name") or PROVIDER_NAME,
            fallback_region=request.region,
            fallback_category=request.category,
            topic_bundle=request.topic_bundle,
            trend_score=6 if request.mode == "priority" else 2,
        )
        if item:
            results.append(item)

    return results
