from collections import Counter

from app.config import get_settings
from app.priority_topics import MOROCCO_SCOPE_TERMS, build_topic_query
from app.providers.common import FetchRequest, normalize_article, request_json


PROVIDER_NAME = "GDELT"
BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def fetch_general(request: FetchRequest) -> list[dict]:
    settings = get_settings()
    if not settings.gdelt_enabled:
        return []

    query = (
        "(Morocco OR Rabat OR Casablanca OR Tangier)"
        if request.region == "ma"
        else "(world OR international OR diplomacy OR crisis)"
    )

    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "sort": "DateDesc",
        "timespan": "48h",
        "maxrecords": min(request.limit, settings.gdelt_max_records),
    }

    data = request_json(
        BASE_URL,
        params=params,
        timeout=settings.request_timeout_seconds,
    )
    if not data:
        return []

    return _normalize_articles(data.get("articles", []), request, default_trend=4)


def fetch_priority(request: FetchRequest) -> list[dict]:
    settings = get_settings()
    if not settings.gdelt_enabled or not request.topic_bundle:
        return []

    query = build_topic_query(request.topic_bundle, request.region)
    if request.region == "ma" and not request.topic_bundle.region_scope_terms:
        scope_terms = " OR ".join(MOROCCO_SCOPE_TERMS)
        query = f"({scope_terms}) AND ({query})"

    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "sort": "DateDesc",
        "timespan": "72h",
        "maxrecords": min(request.limit, settings.gdelt_max_records),
    }

    data = request_json(
        BASE_URL,
        params=params,
        timeout=settings.request_timeout_seconds,
    )
    if not data:
        return []

    return _normalize_articles(data.get("articles", []), request, default_trend=9)


def fetch_trend_signals(region: str, topic_bundles: list) -> list[dict]:
    settings = get_settings()
    if not settings.gdelt_enabled:
        return []

    signals = []

    for bundle in topic_bundles:
        query = build_topic_query(bundle, region)
        if region == "ma" and not bundle.region_scope_terms:
            scope_terms = " OR ".join(MOROCCO_SCOPE_TERMS)
            query = f"({scope_terms}) AND ({query})"

        timeline_params = {
            "query": query,
            "mode": "TimelineVolRaw",
            "format": "json",
            "TIMELINESMOOTH": 0,
            "timespan": "72h",
        }

        timeline_data = request_json(
            BASE_URL,
            params=timeline_params,
            timeout=settings.request_timeout_seconds,
        )

        points = timeline_data.get("timeline", []) if timeline_data else []
        values = []
        for point in points:
            value = point.get("value")
            if value is None:
                value = point.get("count") or point.get("norm")
            try:
                values.append(float(value))
            except (TypeError, ValueError):
                continue

        volume = int(max(values)) if values else 0

        if volume == 0:
            article_probe = fetch_priority(
                FetchRequest(
                    region=region,
                    mode="priority",
                    limit=min(6, settings.gdelt_max_records),
                    category=bundle.category,
                    topic_bundle=bundle,
                )
            )
            volume = len(article_probe)

        if volume > 0:
            signals.append(
                {
                    "topic": bundle.label,
                    "topic_slug": bundle.slug,
                    "region": region,
                    "volume": volume,
                    "priority_weight": bundle.priority_weight,
                    "conflict_related": bundle.conflict_related,
                }
            )

    return signals


def _normalize_articles(raw_articles: list[dict], request: FetchRequest, default_trend: float) -> list[dict]:
    results = []
    seen = Counter()

    for article in raw_articles:
        title = article.get("title") or article.get("seendate") or ""
        url = article.get("url") or ""
        if not title or not url:
            continue

        item = normalize_article(
            provider_name=PROVIDER_NAME,
            title=title,
            description=article.get("socialimage") or article.get("domain") or title,
            url=url,
            published_at=article.get("seendate") or article.get("date") or "",
            source_name=article.get("domain") or PROVIDER_NAME,
            image_url=article.get("socialimage") or article.get("image") or "",
            fallback_region=request.region,
            fallback_category=request.category,
            topic_bundle=request.topic_bundle,
            trend_score=default_trend,
        )
        if not item:
            continue

        seen[item["url"]] += 1
        if seen[item["url"]] > 1:
            continue

        results.append(item)

    return results
