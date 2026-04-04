from collections import Counter, defaultdict
from datetime import datetime, timezone

from app.config import get_settings
from app.trend_providers.common import (
    TrendProviderResult,
    TrendSignal,
    freshness_score_from_timestamp,
    normalize_topic,
    request_json,
)


PROVIDER_NAME = "Reddit"

REGION_SUBREDDITS = {
    "world": ("worldnews", "news", "geopolitics"),
    "ma": ("Morocco", "africa"),
}


def collect_trends(region: str) -> TrendProviderResult:
    settings = get_settings()
    if not settings.reddit_enabled:
        return TrendProviderResult(
            provider_name=PROVIDER_NAME,
            status="unavailable",
            signals=[],
            note="Reddit trend collection is disabled by configuration.",
        )

    posts = []
    headers = {"User-Agent": settings.reddit_user_agent}

    for subreddit in REGION_SUBREDDITS.get(region, ()):
        data = request_json(
            f"https://www.reddit.com/r/{subreddit}/hot.json",
            params={"limit": settings.social_trend_limit},
            headers=headers,
            timeout=settings.trend_provider_timeout_seconds,
        )
        if not data:
            continue

        for child in data.get("data", {}).get("children", []):
            post = child.get("data") or {}
            posts.append(
                {
                    "title": post.get("title", ""),
                    "score": float(post.get("score") or 0),
                    "comments": float(post.get("num_comments") or 0),
                    "created_at": datetime.fromtimestamp(
                        float(post.get("created_utc") or datetime.now(timezone.utc).timestamp()),
                        tz=timezone.utc,
                    ).isoformat(),
                }
            )

    if not posts:
        return TrendProviderResult(
            provider_name=PROVIDER_NAME,
            status="unavailable",
            signals=[],
            note="Reddit did not return usable trend posts for this region.",
        )

    grouped = defaultdict(list)
    display_titles = Counter()

    for post in posts:
        normalized = normalize_topic(post["title"])
        if not normalized:
            continue
        grouped[normalized].append(post)
        display_titles[(normalized, post["title"])] += 1

    signals = []

    for normalized, related_posts in grouped.items():
        total_score = sum(post["score"] for post in related_posts)
        total_comments = sum(post["comments"] for post in related_posts)
        latest_timestamp = max(post["created_at"] for post in related_posts)
        display_title = max(
            (key for key in display_titles if key[0] == normalized),
            key=lambda key: display_titles[key],
        )[1]

        virality = min(100.0, (total_score / 80.0) + (total_comments / 15.0))
        signals.append(
            TrendSignal(
                title=display_title,
                normalized_topic=normalized,
                region=region,
                provider_name=PROVIDER_NAME,
                signal_type="social",
                score=virality,
                volume=total_score + total_comments,
                recency_score=freshness_score_from_timestamp(latest_timestamp),
                confidence=0.72,
                platform="reddit",
                related_articles_count=len(related_posts),
                verification_score=0.0,
                note="Derived from Reddit hot posts.",
            )
        )

    return TrendProviderResult(
        provider_name=PROVIDER_NAME,
        status="available",
        signals=sorted(signals, key=lambda item: item.score, reverse=True)[: settings.social_trend_limit],
        note="Reddit social trend signal collected successfully.",
    )
