from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Optional

import requests


GENERIC_TREND_TOKENS = {
    "after",
    "amid",
    "breaking",
    "current",
    "global",
    "headline",
    "live",
    "major",
    "more",
    "news",
    "report",
    "reports",
    "says",
    "saying",
    "story",
    "this",
    "today",
    "update",
    "updates",
    "world",
}


@dataclass(frozen=True)
class TrendSignal:
    title: str
    normalized_topic: str
    region: str
    provider_name: str
    signal_type: str
    score: float
    volume: float
    recency_score: float
    confidence: float
    platform: str
    related_articles_count: int = 0
    verification_score: float = 0.0
    note: str = ""
    media_type: str = "text"
    thumbnail_url: str = ""
    source_url: str = ""
    verification_status: str = "unverified"
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class TrendProviderResult:
    provider_name: str
    status: str
    signals: list[TrendSignal]
    note: str = ""


def normalize_topic(value: str) -> str:
    tokens = re.findall(r"[a-zA-Z0-9']+", (value or "").lower())
    filtered = [token for token in tokens if len(token) > 2 and token not in GENERIC_TREND_TOKENS]
    return "-".join(filtered[:6])


def display_title_from_topic(value: str) -> str:
    topic = (value or "").replace("-", " ").strip()
    return topic.title() if topic else "Untitled Trend"


def freshness_score_from_timestamp(timestamp: str | None) -> float:
    if not timestamp:
        return 1.0

    try:
        published_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return 1.0

    age_hours = max(0.0, (datetime.now(timezone.utc) - published_at).total_seconds() / 3600)
    if age_hours <= 2:
        return 10.0
    if age_hours <= 6:
        return 8.0
    if age_hours <= 12:
        return 6.0
    if age_hours <= 24:
        return 4.0
    return 2.0


def request_json(url: str, *, params: Optional[dict] = None, headers: Optional[dict] = None, timeout: int = 8):
    try:
        response = requests.get(url, params=params, headers=headers or {}, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return None
