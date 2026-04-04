from app.config import get_settings
from app.priority_topics import MOROCCO_SCOPE_TERMS, build_topic_query
from app.providers.common import FetchRequest, normalize_article, request_json, strip_html


PROVIDER_NAME = "Guardian"
BASE_URL = "https://content.guardianapis.com/search"


def fetch_general(request: FetchRequest) -> list[dict]:
    settings = get_settings()
    query = "Morocco OR Rabat OR Casablanca" if request.region == "ma" else "world OR diplomacy"

    params = {
        "api-key": settings.guardian_api_key or "test",
        "page-size": request.limit,
        "show-fields": "trailText",
        "order-by": "newest",
        "q": query,
    }

    data = request_json(
        BASE_URL,
        params=params,
        timeout=settings.request_timeout_seconds,
    )
    if not data:
        return []

    return _normalize_articles(data.get("response", {}).get("results", []), request)


def fetch_priority(request: FetchRequest) -> list[dict]:
    settings = get_settings()
    if not request.topic_bundle:
        return []

    query = build_topic_query(request.topic_bundle, request.region)
    if request.region == "ma" and not request.topic_bundle.region_scope_terms:
        scope_terms = " OR ".join(MOROCCO_SCOPE_TERMS)
        query = f"({scope_terms}) AND ({query})"

    params = {
        "api-key": settings.guardian_api_key or "test",
        "page-size": request.limit,
        "show-fields": "trailText",
        "order-by": "newest",
        "q": query,
    }

    data = request_json(
        BASE_URL,
        params=params,
        timeout=settings.request_timeout_seconds,
    )
    if not data:
        return []

    return _normalize_articles(data.get("response", {}).get("results", []), request)


def _normalize_articles(raw_articles: list[dict], request: FetchRequest) -> list[dict]:
    results = []

    for article in raw_articles:
        description = strip_html((article.get("fields") or {}).get("trailText"))
        item = normalize_article(
            provider_name=PROVIDER_NAME,
            title=article.get("webTitle") or "",
            description=description,
            url=article.get("webUrl") or "",
            published_at=article.get("webPublicationDate") or "",
            source_name="The Guardian",
            fallback_region=request.region,
            fallback_category=request.category,
            topic_bundle=request.topic_bundle,
            trend_score=5 if request.mode == "priority" else 2,
        )
        if item:
            results.append(item)

    return results
