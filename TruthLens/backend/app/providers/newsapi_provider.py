from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.priority_topics import MOROCCO_SCOPE_TERMS, build_topic_query
from app.providers.common import FetchRequest, normalize_article, request_json


PROVIDER_NAME = "NewsAPI"
BASE_URL = "https://newsapi.org/v2"


def fetch_general(request: FetchRequest) -> list[dict]:
    settings = get_settings()
    if not settings.newsapi_enabled:
        return []

    from_date = (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat()
    queries = (
        [
            "Morocco OR Rabat OR Casablanca OR Tangier OR Marrakech",
            "Morocco economy OR Morocco politics OR Morocco technology OR Morocco health",
        ]
        if request.region == "ma"
        else [
            "world OR international OR global crisis OR diplomacy",
            "conflict OR ceasefire OR humanitarian crisis OR elections OR technology",
        ]
    )

    items = []
    for query in queries:
        params = {
            "apiKey": settings.newsapi_api_key,
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": request.limit,
            "from": from_date,
            "searchIn": "title,description",
        }
        data = request_json(
            f"{BASE_URL}/everything",
            params=params,
            timeout=settings.request_timeout_seconds,
        )
        if not data:
            continue
        items.extend(_normalize_articles(data.get("articles", []), request))

    return items


def fetch_priority(request: FetchRequest) -> list[dict]:
    settings = get_settings()
    if not settings.newsapi_enabled or not request.topic_bundle:
        return []

    from_date = (datetime.now(timezone.utc) - timedelta(days=3)).date().isoformat()
    query = build_topic_query(request.topic_bundle, request.region)

    if request.region == "ma" and not request.topic_bundle.region_scope_terms:
        scope_terms = " OR ".join(MOROCCO_SCOPE_TERMS)
        query = f"({scope_terms}) AND ({query})"

    params = {
        "apiKey": settings.newsapi_api_key,
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max(request.limit, 12),
        "from": from_date,
        "searchIn": "title,description",
    }

    data = request_json(
        f"{BASE_URL}/everything",
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
            image_url=article.get("urlToImage") or "",
            fallback_region=request.region,
            fallback_category=request.category,
            topic_bundle=request.topic_bundle,
            trend_score=7 if request.mode == "priority" else 3,
        )
        if item:
            results.append(item)

    return results
