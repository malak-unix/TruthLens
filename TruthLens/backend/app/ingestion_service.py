from collections import Counter
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from xml.etree import ElementTree
import re

import requests

from app.analyzer import analyze_payload
from app.config import get_settings
from app.database import (
    get_connection,
    save_refresh_log,
    store_trending_topics,
    upsert_news_items,
)
from app.source_registry import (
    MOROCCO_RSS_SOURCES,
    WORLD_RSS_SOURCES,
    get_source_profile,
)


STOPWORDS = {
    "the", "and", "for", "with", "that", "from", "this", "into", "about", "after",
    "have", "will", "says", "said", "more", "than", "over", "under", "amid",
    "news", "new", "world", "morocco", "moroccan", "rabat", "casablanca", "video",
    "claim", "claims", "update", "official", "report", "reports", "breaking",
}


def sanitize_text(value: str | None, fallback: str = "") -> str:
    text = unescape((value or "").strip())
    text = " ".join(text.split())
    return text or fallback


def strip_html(value: str | None) -> str:
    raw = sanitize_text(value, "")
    output = []
    inside_tag = False

    for char in raw:
        if char == "<":
            inside_tag = True
            continue
        if char == ">":
            inside_tag = False
            continue
        if not inside_tag:
            output.append(char)

    return " ".join("".join(output).split())


def parse_iso_timestamp(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except ValueError:
        return datetime.now(timezone.utc).isoformat()


def parse_rss_timestamp(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()

    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def detect_category(title: str, description: str, fallback: str = "International") -> str:
    haystack = f"{title} {description}".lower()

    rules = {
        "Politics": ["election", "minister", "parliament", "government", "president"],
        "Economy": ["economy", "market", "trade", "bank", "inflation", "tariff", "tax"],
        "Technology": ["ai", "cyber", "technology", "software", "chip", "tech"],
        "Health": ["health", "hospital", "vaccine", "medical", "disease"],
        "Sports": ["sport", "football", "soccer", "match", "team", "league"],
        "Society": ["education", "community", "family", "housing", "migration", "school"],
    }

    for category, keywords in rules.items():
        if any(keyword in haystack for keyword in keywords):
            return category

    return fallback


def is_morocco_relevant(title: str, description: str, url: str, source_name: str) -> bool:
    haystack = f"{title} {description} {source_name} {url}".lower()
    terms = [
        "morocco",
        "moroccan",
        "rabat",
        "casablanca",
        "fes",
        "marrakech",
        "tangier",
        "agadir",
        "king mohammed",
        ".ma",
    ]
    return any(term in haystack for term in terms)


def build_news_item(
    title: str,
    description: str,
    url: str,
    published_at: str,
    source_name: str,
    fallback_region: str,
    fallback_category: str,
):
    title = sanitize_text(title, "Untitled article")
    description = sanitize_text(description, title)
    url = sanitize_text(url)
    source_name = sanitize_text(source_name, "Unknown source")

    if not url:
        return None

    profile = get_source_profile(url=url, source_name=source_name)
    region = profile.get("region", fallback_region)

    if fallback_region == "ma" or is_morocco_relevant(title, description, url, source_name):
        region = "ma"

    category = detect_category(title, description, fallback_category)

    # Important: pendant l’ingestion on n’analyse PAS l’URL complète
    # sinon le refresh devient lent et fragile.
    analysis = analyze_payload(
        text=f"{title}. {description}",
        source_name=source_name,
    )

    return {
        "title": title,
        "source_name": source_name,
        "published_at": published_at,
        "country": region,
        "category": category,
        "url": url,
        "description": description,
        "credibility_score": analysis["credibility_score"],
        "credibility_label": analysis["credibility_label"],
        "explanation": analysis["explanation"],
        "source_type": profile.get("source_type", "discovery"),
        "source_trust_level": profile.get("trust_level", "unknown"),
        "language": profile.get("language", "unknown"),
    }


def parse_rss_items(xml_text: str) -> list[dict]:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return []

    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item in channel.findall("item"):
        items.append(
            {
                "title": item.findtext("title"),
                "description": strip_html(item.findtext("description")),
                "url": item.findtext("link"),
                "published_at": item.findtext("pubDate"),
            }
        )

    return items


def fetch_rss_sources() -> tuple[list[dict], int]:
    settings = get_settings()
    headers = {"User-Agent": "TruthLens/1.0"}
    items: list[dict] = []
    failed = 0

    for source in [*MOROCCO_RSS_SOURCES, *WORLD_RSS_SOURCES]:
        try:
            response = requests.get(
                source["url"],
                headers=headers,
                timeout=settings.rss_timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException:
            failed += 1
            continue

        feed_items = parse_rss_items(response.text)[: max(1, settings.default_refresh_limit // 2)]

        for raw in feed_items:
            news_item = build_news_item(
                title=raw.get("title") or "",
                description=raw.get("description") or "",
                url=raw.get("url") or "",
                published_at=parse_rss_timestamp(raw.get("published_at")),
                source_name=source["name"],
                fallback_region=source["region"],
                fallback_category=source["category"],
            )
            if news_item:
                items.append(news_item)

    return items, failed


def fetch_newsapi_news() -> tuple[list[dict], int]:
    settings = get_settings()
    if not settings.newsapi_enabled:
        return [], 0

    from_date = (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat()
    queries = [
        {
            "params": {
                "apiKey": settings.newsapi_api_key,
                "q": "Morocco OR Rabat OR Casablanca",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": settings.default_refresh_limit,
                "from": from_date,
            },
            "region": "ma",
        },
        {
            "params": {
                "apiKey": settings.newsapi_api_key,
                "q": "world OR international",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": settings.default_refresh_limit,
                "from": from_date,
            },
            "region": "world",
        },
    ]

    all_items: list[dict] = []
    failed = 0

    for query in queries:
        try:
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params=query["params"],
                headers={"User-Agent": "TruthLens/1.0"},
                timeout=settings.request_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            failed += 1
            continue

        for article in data.get("articles", []):
            url = sanitize_text(article.get("url"))
            if not url:
                continue

            title = article.get("title") or ""
            description = article.get("description") or ""
            source_name = (article.get("source") or {}).get("name") or "NewsAPI"

            if query["region"] == "ma" and not is_morocco_relevant(title, description, url, source_name):
                continue

            news_item = build_news_item(
                title=title,
                description=description,
                url=url,
                published_at=parse_iso_timestamp(article.get("publishedAt")),
                source_name=source_name,
                fallback_region=query["region"],
                fallback_category="International",
            )
            if news_item:
                all_items.append(news_item)

    return all_items, failed


def fetch_gnews_news() -> tuple[list[dict], int]:
    settings = get_settings()
    if not settings.gnews_enabled:
        return [], 0

    queries = [
        {
            "params": {
                "token": settings.gnews_api_key,
                "lang": "en",
                "country": "ma",
                "max": settings.default_refresh_limit,
            },
            "region": "ma",
        },
        {
            "params": {
                "token": settings.gnews_api_key,
                "lang": "en",
                "topic": "world",
                "max": settings.default_refresh_limit,
            },
            "region": "world",
        },
    ]

    all_items: list[dict] = []
    failed = 0

    for query in queries:
        try:
            response = requests.get(
                "https://gnews.io/api/v4/top-headlines",
                params=query["params"],
                headers={"User-Agent": "TruthLens/1.0"},
                timeout=settings.request_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            failed += 1
            continue

        for article in data.get("articles", []):
            url = sanitize_text(article.get("url"))
            if not url:
                continue

            title = article.get("title") or ""
            description = article.get("description") or ""
            source_name = (article.get("source") or {}).get("name") or "GNews"

            if query["region"] == "ma" and not is_morocco_relevant(title, description, url, source_name):
                continue

            news_item = build_news_item(
                title=title,
                description=description,
                url=url,
                published_at=parse_iso_timestamp(article.get("publishedAt")),
                source_name=source_name,
                fallback_region=query["region"],
                fallback_category="International",
            )
            if news_item:
                all_items.append(news_item)

    return all_items, failed


def dedupe_news(items: list[dict]) -> list[dict]:
    deduped: dict[str, dict] = {}

    for item in items:
        key = item["url"].strip().lower()
        if not key:
            continue

        existing = deduped.get(key)
        if existing is None or item["published_at"] > existing["published_at"]:
            deduped[key] = item

    return sorted(deduped.values(), key=lambda x: x["published_at"], reverse=True)


def re_split_words(text: str) -> list[str]:
    return re.findall(r"[a-zA-ZÀ-ÿ0-9']+", text)


def compute_trending_topics(items: list[dict]) -> list[dict]:
    grouped = {"ma": [], "world": []}
    for item in items:
        grouped.setdefault(item["country"], []).append(item)

    results = []

    for region, region_items in grouped.items():
        token_counter = Counter()

        for item in region_items:
            text = f"{item['title']} {item['description']}".lower()
            words = re_split_words(text)
            unique_words = {
                word
                for word in words
                if len(word) > 3 and word not in STOPWORDS
            }
            token_counter.update(unique_words)

        for topic, count in token_counter.most_common(6):
            related = [
                item
                for item in region_items
                if topic in f"{item['title']} {item['description']}".lower()
            ]

            avg_score = (
                int(sum(item["credibility_score"] for item in related) / len(related))
                if related
                else 0
            )

            results.append(
                {
                    "topic": topic.title(),
                    "region": region,
                    "intensity": min(100, count * 15),
                    "article_count": len(related),
                    "freshness": "fresh" if related else "unknown",
                    "credibility_warning": avg_score < 50 and len(related) >= 2,
                }
            )

    return sorted(results, key=lambda x: x["intensity"], reverse=True)[:12]


def run_ingestion_pipeline(batch_label: str) -> dict:
    started_at = datetime.now(timezone.utc).isoformat()

    all_items: list[dict] = []
    failed_source_count = 0

    try:
        newsapi_items, newsapi_failed = fetch_newsapi_news()
        all_items.extend(newsapi_items)
        failed_source_count += newsapi_failed
    except Exception as exc:
        print(f"[TruthLens] NewsAPI fetch failed: {exc}")
        failed_source_count += 1

    try:
        gnews_items, gnews_failed = fetch_gnews_news()
        all_items.extend(gnews_items)
        failed_source_count += gnews_failed
    except Exception as exc:
        print(f"[TruthLens] GNews fetch failed: {exc}")
        failed_source_count += 1

    try:
        rss_items, rss_failed = fetch_rss_sources()
        all_items.extend(rss_items)
        failed_source_count += rss_failed
    except Exception as exc:
        print(f"[TruthLens] RSS fetch failed: {exc}")
        failed_source_count += 1

    all_items = dedupe_news(all_items)
    trending_topics = compute_trending_topics(all_items) if all_items else []

    conn = get_connection()
    cursor = conn.cursor()

    inserted_count, duplicate_count = upsert_news_items(cursor, all_items, batch_label)

    if trending_topics:
        store_trending_topics(cursor, trending_topics)

    finished_at = datetime.now(timezone.utc).isoformat()

    save_refresh_log(
        cursor=cursor,
        batch_label=batch_label,
        started_at=started_at,
        finished_at=finished_at,
        inserted_count=inserted_count,
        duplicate_count=duplicate_count,
        failed_source_count=failed_source_count,
        trend_update_count=len(trending_topics),
    )

    conn.commit()
    conn.close()

    return {
        "batch_label": batch_label,
        "started_at": started_at,
        "finished_at": finished_at,
        "inserted_count": inserted_count,
        "duplicate_count": duplicate_count,
        "failed_source_count": failed_source_count,
        "trend_update_count": len(trending_topics),
        "total_items_processed": len(all_items),
    }