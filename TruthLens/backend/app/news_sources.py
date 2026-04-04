from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Iterable
from urllib.parse import urlparse
from xml.etree import ElementTree
import re

import requests

from app.analyzer import analyze_text_content
from app.config import get_settings

STATIC_NEWS = [
    {
        "title": "New Economic Policy Announced: Major Changes to Tax System",
        "source_name": "Le Matin",
        "published_at": "2026-04-02T10:00:00+00:00",
        "country": "ma",
        "category": "Economy",
        "url": "https://example.com/ma-tax-policy",
        "description": "Verified by official government sources and confirmed by multiple independent journalists.",
        "credibility_score": 85,
        "credibility_label": "Reliable",
        "explanation": "Source is established, article has institutional context, and the claim appears corroborated.",
    },
    {
        "title": "Healthcare Reform Bill Passes Parliament with Unanimous Support",
        "source_name": "Morocco Today",
        "published_at": "2026-04-02T07:30:00+00:00",
        "country": "ma",
        "category": "Health",
        "url": "https://example.com/ma-health-bill",
        "description": "Confirmed by parliamentary records and cross-verified with multiple reports.",
        "credibility_score": 92,
        "credibility_label": "Reliable",
        "explanation": "Article references institutional action and includes enough context.",
    },
    {
        "title": "Casablanca Tech Forum Highlights AI for Public Services",
        "source_name": "MAP News",
        "published_at": "2026-04-02T09:10:00+00:00",
        "country": "ma",
        "category": "Technology",
        "url": "https://example.com/ma-ai-forum",
        "description": "Multiple speakers and organizers confirmed the event details.",
        "credibility_score": 81,
        "credibility_label": "Reliable",
        "explanation": "Recognized source, clear context, and multiple confirmatory signals.",
    },
    {
        "title": "Viral Claim Says Water Supply Will Be Cut Across Rabat Tomorrow",
        "source_name": "Unknown Facebook Relay",
        "published_at": "2026-04-02T08:00:00+00:00",
        "country": "ma",
        "category": "Society",
        "url": "https://example.com/ma-water-rumor",
        "description": "The claim is spreading online without official statement or source attribution.",
        "credibility_score": 22,
        "credibility_label": "Suspicious",
        "explanation": "Weak source and missing official confirmation make the claim doubtful.",
    },
    {
        "title": "Major Sports Event Postponed Due to Weather Conditions",
        "source_name": "Sports Gazette",
        "published_at": "2026-04-02T06:00:00+00:00",
        "country": "world",
        "category": "Sports",
        "url": "https://example.com/world-sports-delay",
        "description": "Awaiting official confirmation from event organizers. Only reported by one source.",
        "credibility_score": 45,
        "credibility_label": "Unverified",
        "explanation": "Single-source reporting and missing official confirmation reduce confidence.",
    },
    {
        "title": "Viral Video Claims Government Cover-up of Major Incident",
        "source_name": "Unknown Blog",
        "published_at": "2026-04-02T05:00:00+00:00",
        "country": "world",
        "category": "Politics",
        "url": "https://example.com/viral-coverup",
        "description": "Sensational wording, no clear evidence, no reliable corroboration.",
        "credibility_score": 18,
        "credibility_label": "High Risk",
        "explanation": "The article uses alarmist language, unclear sourcing, and lacks corroboration.",
    },
    {
        "title": "WHO Releases New Guidance on Global Vaccination Priorities",
        "source_name": "WHO",
        "published_at": "2026-04-02T04:40:00+00:00",
        "country": "world",
        "category": "Health",
        "url": "https://example.com/world-who-guidance",
        "description": "Published through an institutional channel with structured supporting information.",
        "credibility_score": 90,
        "credibility_label": "Reliable",
        "explanation": "Institutional source and formal publication context increase confidence.",
    },
    {
        "title": "International Markets React to Overnight Policy Announcements",
        "source_name": "Reuters",
        "published_at": "2026-04-02T03:50:00+00:00",
        "country": "world",
        "category": "Economy",
        "url": "https://example.com/world-market-reaction",
        "description": "The development is reported by a recognized global news organization.",
        "credibility_score": 84,
        "credibility_label": "Reliable",
        "explanation": "Known source, structured reporting, and coherent context support credibility.",
    },
]

CNN_RSS_FEEDS = [
    {"url": "http://rss.cnn.com/rss/edition.rss", "category": "International"},
    {"url": "http://rss.cnn.com/rss/edition_world.rss", "category": "International"},
    {"url": "http://rss.cnn.com/rss/edition_business.rss", "category": "Economy"},
    {"url": "http://rss.cnn.com/rss/edition_technology.rss", "category": "Technology"},
    {"url": "http://rss.cnn.com/rss/edition_health.rss", "category": "Health"},
    {"url": "http://rss.cnn.com/rss/edition_sport.rss", "category": "Sports"},
]


def sanitize_text(value: str | None, fallback: str) -> str:
    normalized = unescape((value or "").strip())
    return normalized or fallback


def strip_html(value: str | None) -> str:
    text = sanitize_text(value, "")
    inside_tag = False
    chars = []

    for char in text:
        if char == "<":
            inside_tag = True
            continue
        if char == ">":
            inside_tag = False
            continue
        if not inside_tag:
            chars.append(char)

    cleaned = "".join(chars)
    return " ".join(cleaned.split())


def parse_rss_timestamp(raw_value: str | None) -> str:
    if not raw_value:
        return datetime.now(timezone.utc).isoformat()

    try:
        return parsedate_to_datetime(raw_value).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return datetime.now(timezone.utc).isoformat()


def parse_iso_timestamp(raw_value: str | None) -> str:
    if not raw_value:
        return datetime.now(timezone.utc).isoformat()

    normalized = raw_value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).astimezone(timezone.utc).isoformat()
    except ValueError:
        return datetime.now(timezone.utc).isoformat()


def is_recent_timestamp(iso_value: str, max_age_days: int = 30) -> bool:
    try:
        published_at = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
    except ValueError:
        return False

    age = datetime.now(timezone.utc) - published_at.astimezone(timezone.utc)
    return age.days <= max_age_days


def detect_country(title: str, description: str, fallback: str) -> str:
    haystack = f"{title} {description}".lower()
    morocco_terms = ["morocco", "moroccan", "casablanca", "rabat", "tangier", "marrakesh", "fes"]
    if any(term in haystack for term in morocco_terms):
        return "ma"
    return fallback


def is_morocco_relevant(title: str, description: str, url: str, source_name: str) -> bool:
    haystack = f"{title} {description} {source_name}".lower()
    hostname = urlparse(url).netloc.lower().replace("www.", "")
    morocco_patterns = [
        r"\bmorocco\b",
        r"\bmoroccan\b",
        r"\bcasablanca\b",
        r"\brabat\b",
        r"\btangier\b",
        r"\bmarrakesh\b",
        r"\bfes\b",
        r"\bagadir\b",
        r"\bchefchaouen\b",
        r"\bking mohammed\b",
    ]
    local_hosts = [
        "lematin.ma",
        "mapnews.ma",
        "hespress.com",
        "moroccoworldnews.com",
        "moroccotoday.net",
    ]
    local_sources = [
        "le matin",
        "map news",
        "hespress",
        "morocco world news",
        "morocco today",
    ]

    if any(host in hostname for host in local_hosts):
        return True

    if any(source in haystack for source in local_sources):
        return True

    return any(re.search(pattern, haystack) for pattern in morocco_patterns)


def assign_country(title: str, description: str, url: str, source_name: str, requested_country: str) -> str:
    if requested_country == "ma":
        return "ma" if is_morocco_relevant(title, description, url, source_name) else "world"

    detected_country = detect_country(title, description, "world")
    return detected_country if detected_country == "ma" else requested_country


def detect_category(title: str, description: str, fallback: str) -> str:
    haystack = f"{title} {description}".lower()
    category_rules = {
        "Politics": ["election", "president", "minister", "parliament", "senate", "government", "indictment"],
        "Economy": ["market", "economy", "trade", "tariff", "stocks", "business", "inflation", "tax", "bank"],
        "Technology": ["ai", "technology", "tech", "software", "cyber", "chip", "device"],
        "Health": ["health", "hospital", "vaccine", "disease", "medical", "who"],
        "Sports": ["sport", "football", "soccer", "olympic", "match", "team", "nba", "ufc"],
        "Society": ["school", "education", "family", "community", "migration", "housing"],
        "International": ["world", "global", "international"],
    }

    for category, keywords in category_rules.items():
        if any(keyword in haystack for keyword in keywords):
            return category

    return fallback


def build_news_item(
    title: str,
    description: str,
    url: str,
    published_at: str,
    source_name: str,
    country: str,
    category: str,
) -> dict:
    effective_title = sanitize_text(title, "Untitled article")
    effective_description = sanitize_text(description, effective_title)
    effective_url = sanitize_text(url, "https://example.com/unavailable")
    effective_source = sanitize_text(source_name, "Unknown source")
    effective_country = assign_country(
        effective_title,
        effective_description,
        effective_url,
        effective_source,
        country,
    )
    effective_category = detect_category(effective_title, effective_description, category)
    analysis = analyze_text_content(
        " ".join(
            [
                effective_title,
                effective_description,
                effective_url,
                effective_source,
                effective_category,
            ]
        )
    )

    return {
        "title": effective_title,
        "source_name": effective_source,
        "published_at": published_at,
        "country": effective_country,
        "category": effective_category,
        "url": effective_url,
        "description": effective_description,
        "credibility_score": analysis["credibility_score"],
        "credibility_label": analysis["credibility_label"],
        "explanation": analysis["explanation"],
    }


def parse_rss_items(xml_text: str) -> Iterable[dict]:
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


def fetch_json(url: str, params: dict, timeout_seconds: int) -> dict | None:
    headers = {"User-Agent": "TruthLens/1.0"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout_seconds)
        response.raise_for_status()
    except requests.RequestException:
        return None

    try:
        return response.json()
    except ValueError:
        return None


def fetch_cnn_news(timeout_seconds: int = 3, per_feed_limit: int = 2) -> list[dict]:
    headers = {"User-Agent": "TruthLens/1.0"}
    collected = []
    seen_urls = set()

    for feed in CNN_RSS_FEEDS:
        try:
            response = requests.get(feed["url"], headers=headers, timeout=timeout_seconds)
            response.raise_for_status()
        except requests.RequestException:
            continue

        count = 0
        for item in parse_rss_items(response.text):
            url = sanitize_text(item.get("url"), "")
            if not url or url in seen_urls:
                continue

            parsed_url = urlparse(url)
            if "cnn.com" not in parsed_url.netloc and "cnn.it" not in parsed_url.netloc:
                continue

            published_at = parse_rss_timestamp(item.get("published_at"))
            if not is_recent_timestamp(published_at):
                continue

            seen_urls.add(url)
            collected.append(
                build_news_item(
                    title=item.get("title") or "",
                    description=item.get("description") or "",
                    url=url,
                    published_at=published_at,
                    source_name="CNN",
                    country="world",
                    category=feed["category"],
                )
            )
            count += 1

            if count >= per_feed_limit:
                break

    return collected


def fetch_gnews_news(timeout_seconds: int = 5, max_per_query: int = 4) -> list[dict]:
    settings = get_settings()
    if not settings.gnews_enabled:
        return []

    queries = [
        {
            "params": {
                "token": settings.gnews_api_key,
                "lang": "en",
                "country": "ma",
                "q": "Morocco OR Rabat OR Casablanca",
                "max": max_per_query,
            },
            "country": "ma",
            "fallback_category": "International",
        },
        {
            "params": {
                "token": settings.gnews_api_key,
                "lang": "en",
                "topic": "world",
                "max": max_per_query,
            },
            "country": "world",
            "fallback_category": "International",
        },
    ]

    collected = []
    for query in queries:
        data = fetch_json("https://gnews.io/api/v4/top-headlines", query["params"], timeout_seconds)
        if not data:
            continue

        for article in data.get("articles", []):
            url = sanitize_text(article.get("url"), "")
            if not url:
                continue

            title = article.get("title") or ""
            description = article.get("description") or ""
            source_name = (article.get("source") or {}).get("name") or "GNews"
            if query["country"] == "ma" and not is_morocco_relevant(title, description, url, source_name):
                continue

            collected.append(
                build_news_item(
                    title=title,
                    description=description,
                    url=url,
                    published_at=parse_iso_timestamp(article.get("publishedAt")),
                    source_name=source_name,
                    country=query["country"],
                    category=query["fallback_category"],
                )
            )

    return collected


def fetch_guardian_news(timeout_seconds: int = 5, page_size: int = 6) -> list[dict]:
    settings = get_settings()
    if not settings.guardian_enabled:
        return []

    collected = []
    queries = [
        {"q": "Morocco OR Rabat OR Casablanca", "country": "ma"},
        {"q": "world", "country": "world"},
    ]

    for query in queries:
        data = fetch_json(
            "https://content.guardianapis.com/search",
            {
                "api-key": settings.guardian_api_key,
                "page-size": page_size,
                "show-fields": "trailText",
                "order-by": "newest",
                "q": query["q"],
            },
            timeout_seconds,
        )
        if not data:
            continue

        for article in data.get("response", {}).get("results", []):
            description = strip_html((article.get("fields") or {}).get("trailText"))
            title = article.get("webTitle") or ""
            url = article.get("webUrl") or ""
            source_name = "The Guardian"

            if query["country"] == "ma" and not is_morocco_relevant(title, description, url, source_name):
                continue

            collected.append(
                build_news_item(
                    title=title,
                    description=description,
                    url=url,
                    published_at=parse_iso_timestamp(article.get("webPublicationDate")),
                    source_name=source_name,
                    country=query["country"],
                    category=detect_category(article.get("sectionName") or "", description, "International"),
                )
            )

    return collected


def fetch_newsapi_news(timeout_seconds: int = 5, page_size: int = 4) -> list[dict]:
    settings = get_settings()
    if not settings.newsapi_enabled:
        return []

    from_date = (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat()
    queries = [
        {
            "params": {
                "apiKey": settings.newsapi_api_key,
                "q": "Morocco OR Rabat OR Casablanca",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": page_size,
                "from": from_date,
            },
            "country": "ma",
        },
        {
            "params": {
                "apiKey": settings.newsapi_api_key,
                "q": "world OR international",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": page_size,
                "from": from_date,
            },
            "country": "world",
        },
    ]

    collected = []
    for query in queries:
        data = fetch_json("https://newsapi.org/v2/everything", query["params"], timeout_seconds)
        if not data:
            continue

        for article in data.get("articles", []):
            url = sanitize_text(article.get("url"), "")
            if not url:
                continue

            title = article.get("title") or ""
            description = article.get("description") or ""
            source_name = (article.get("source") or {}).get("name") or "NewsAPI"
            if query["country"] == "ma" and not is_morocco_relevant(title, description, url, source_name):
                continue

            collected.append(
                build_news_item(
                    title=title,
                    description=description,
                    url=url,
                    published_at=parse_iso_timestamp(article.get("publishedAt")),
                    source_name=source_name,
                    country=query["country"],
                    category="International",
                )
            )

    return collected


def dedupe_news(items: Iterable[dict]) -> list[dict]:
    deduped = {}

    for item in items:
        published_at = item["published_at"]
        if not is_recent_timestamp(published_at, max_age_days=365):
            continue

        url = item["url"]
        existing = deduped.get(url)
        if existing is None or published_at > existing["published_at"]:
            deduped[url] = item

    return sorted(
        deduped.values(),
        key=lambda item: item["published_at"],
        reverse=True,
    )


def get_seed_news(timeout_seconds: int = 5) -> list[dict]:
    dynamic_items = [
        *fetch_gnews_news(timeout_seconds=timeout_seconds),
        *fetch_guardian_news(timeout_seconds=timeout_seconds),
        *fetch_newsapi_news(timeout_seconds=timeout_seconds),
        *fetch_cnn_news(timeout_seconds=3),
    ]
    return dedupe_news([*STATIC_NEWS, *dynamic_items])
