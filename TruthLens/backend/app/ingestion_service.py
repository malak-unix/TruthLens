from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
import logging
import re

from app.config import get_settings
from app.database import (
    get_connection,
    prune_old_news,
    save_refresh_log,
    store_trending_topics,
    upsert_news_items,
)
from app.priority_topics import get_priority_topics
from app.providers import (
    GENERAL_FEED_PROVIDERS,
    PRIORITY_FEED_PROVIDERS,
    TREND_MONITOR_PROVIDERS,
)
from app.providers.common import FetchRequest, title_tokens
from app.source_registry import trust_level_score
from app.trend_engine import build_trend_intelligence


logger = logging.getLogger("truthlens.ingestion")
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)


STOPWORDS = {
    "about",
    "after",
    "amid",
    "breaking",
    "claim",
    "claims",
    "from",
    "have",
    "into",
    "live",
    "major",
    "morocco",
    "moroccan",
    "news",
    "official",
    "report",
    "reports",
    "rabat",
    "said",
    "says",
    "this",
    "update",
    "with",
    "world",
}


def _parse_iso_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat((value or "").replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def _freshness_score(published_at: str) -> float:
    age_hours = max(
        0.0,
        (datetime.now(timezone.utc) - _parse_iso_datetime(published_at)).total_seconds() / 3600,
    )

    if age_hours <= 2:
        return 35
    if age_hours <= 6:
        return 31
    if age_hours <= 12:
        return 27
    if age_hours <= 24:
        return 21
    if age_hours <= 48:
        return 14
    if age_hours <= 72:
        return 9
    return 4


def _title_signature(title: str) -> str:
    tokens = [
        token
        for token in title_tokens(title)
        if len(token) > 3 and token not in STOPWORDS
    ]
    return " ".join(tokens[:8])


def _title_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, (left or "").lower(), (right or "").lower()).ratio()


def _article_preference(item: dict) -> float:
    trust = trust_level_score(item.get("source_trust_level", "unknown"))
    freshness = _freshness_score(item.get("published_at", ""))
    priority = float(item.get("priority_score", 0))
    trend = float(item.get("trend_score", 0))
    completeness = float(item.get("completeness_score", 0))
    corroboration_bonus = 4 if item.get("source_type") in {"wire", "public_agency", "public_broadcaster"} else 0
    return freshness + trust + priority + trend + completeness + corroboration_bonus


def _are_title_duplicates(left: dict, right: dict) -> bool:
    if left.get("country") != right.get("country"):
        return False

    if left.get("priority_topic") and left.get("priority_topic") == right.get("priority_topic"):
        return _title_similarity(left["title"], right["title"]) >= 0.74

    if left.get("dedupe_key") and left.get("dedupe_key") == right.get("dedupe_key"):
        return True

    left_tokens = set(_title_signature(left.get("title", "")).split())
    right_tokens = set(_title_signature(right.get("title", "")).split())
    overlap = len(left_tokens & right_tokens)

    return overlap >= 3 and _title_similarity(left["title"], right["title"]) >= 0.72


def dedupe_articles(items: list[dict]) -> tuple[list[dict], dict]:
    url_deduped = {}
    url_removed = 0

    for item in items:
        item["dedupe_key"] = _title_signature(item.get("title", ""))
        existing = url_deduped.get(item["url"])
        if existing is None:
            url_deduped[item["url"]] = item
            continue

        url_removed += 1
        if _article_preference(item) > _article_preference(existing):
            url_deduped[item["url"]] = item

    title_deduped = []
    title_removed = 0

    for item in sorted(url_deduped.values(), key=_article_preference, reverse=True):
        duplicate_index = next(
            (
                index
                for index, existing in enumerate(title_deduped)
                if _are_title_duplicates(item, existing)
            ),
            None,
        )

        if duplicate_index is None:
            title_deduped.append(item)
            continue

        title_removed += 1
        if _article_preference(item) > _article_preference(title_deduped[duplicate_index]):
            title_deduped[duplicate_index] = item

    return title_deduped, {
        "url_duplicates_removed": url_removed,
        "title_duplicates_removed": title_removed,
    }


def apply_ranking(items: list[dict], trend_signals: list[dict]) -> list[dict]:
    trend_map = {
        (signal["region"], signal["topic"]): signal["volume"]
        for signal in trend_signals
    }

    coverage_by_topic = Counter(item["priority_topic"] for item in items if item.get("priority_topic"))
    coverage_by_signature = Counter(item["dedupe_key"] for item in items if item.get("dedupe_key"))

    for item in items:
        topic_coverage = coverage_by_topic.get(item.get("priority_topic") or "", 0)
        signature_coverage = coverage_by_signature.get(item.get("dedupe_key") or "", 0)
        coverage = max(topic_coverage, signature_coverage)
        item["coverage_score"] = min(16.0, max(0, coverage - 1) * 3.0)

        trend_volume = trend_map.get((item["country"], item.get("priority_topic") or ""), 0)
        item["trend_score"] = min(
            18.0,
            float(item.get("trend_score", 0)) + min(10.0, trend_volume * 0.6) + min(6.0, coverage * 1.2),
        )

        item["ranking_score"] = round(
            _freshness_score(item.get("published_at", ""))
            + trust_level_score(item.get("source_trust_level", "unknown"))
            + float(item.get("priority_score", 0))
            + float(item.get("trend_score", 0))
            + float(item.get("coverage_score", 0))
            + float(item.get("completeness_score", 0)),
            2,
        )

    return sorted(
        items,
        key=lambda item: (item.get("ranking_score", 0), item.get("published_at", "")),
        reverse=True,
    )


def compute_trending_topics(items: list[dict], trend_signals: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for item in items:
        grouped[item["country"]].append(item)

    signal_map = defaultdict(list)
    for signal in trend_signals:
        signal_map[signal["region"]].append(signal)

    results = []

    for region in ("ma", "world"):
        region_items = grouped.get(region, [])
        region_signals = signal_map.get(region, [])

        existing_labels = set()

        priority_groups = defaultdict(list)
        for item in region_items:
            if item.get("priority_topic"):
                priority_groups[item["priority_topic"]].append(item)

        for signal in region_signals:
            matches = priority_groups.get(signal["topic"], [])
            article_count = max(len(matches), signal["volume"])
            if article_count == 0:
                continue

            avg_score = (
                sum(article["credibility_score"] for article in matches) / len(matches)
                if matches
                else 55
            )
            avg_rank = (
                sum(article["ranking_score"] for article in matches) / len(matches)
                if matches
                else signal["priority_weight"]
            )
            latest_published = max(
                [article["published_at"] for article in matches],
                default=datetime.now(timezone.utc).isoformat(),
            )
            age_hours = (
                datetime.now(timezone.utc) - _parse_iso_datetime(latest_published)
            ).total_seconds() / 3600

            results.append(
                {
                    "topic": signal["topic"],
                    "region": region,
                    "intensity": min(100, int(article_count * 10 + signal["volume"] * 2 + avg_rank * 0.35)),
                    "article_count": article_count,
                    "freshness": "fresh" if age_hours <= 8 else "active" if age_hours <= 24 else "watch",
                    "credibility_warning": avg_score < 55,
                }
            )
            existing_labels.add(signal["topic"].lower())

        token_counter = Counter()
        token_scores = defaultdict(list)

        for item in region_items:
            for token in {
                token
                for token in title_tokens(f"{item['title']} {item['description']}")
                if len(token) > 4 and token not in STOPWORDS
            }:
                token_counter[token] += 1
                token_scores[token].append(item)

        for token, count in token_counter.most_common(8):
            if count < 2 or token.lower() in existing_labels:
                continue

            related = token_scores[token]
            avg_rank = sum(item["ranking_score"] for item in related) / len(related)
            avg_score = sum(item["credibility_score"] for item in related) / len(related)
            latest_published = max(item["published_at"] for item in related)
            age_hours = (
                datetime.now(timezone.utc) - _parse_iso_datetime(latest_published)
            ).total_seconds() / 3600

            results.append(
                {
                    "topic": token.title(),
                    "region": region,
                    "intensity": min(100, int(count * 14 + avg_rank * 0.3)),
                    "article_count": len(related),
                    "freshness": "fresh" if age_hours <= 8 else "active" if age_hours <= 24 else "watch",
                    "credibility_warning": avg_score < 50,
                }
            )

    return sorted(
        results,
        key=lambda item: (item["intensity"], item["article_count"]),
        reverse=True,
    )[:12]


def _fetch_general_articles(provider_module, region: str, provider_counts: Counter) -> tuple[list[dict], int]:
    settings = get_settings()
    provider_name = getattr(provider_module, "PROVIDER_NAME", provider_module.__name__)

    try:
        items = provider_module.fetch_general(
            FetchRequest(
                region=region,
                mode="general",
                limit=settings.general_feed_limit,
            )
        )
        provider_counts[provider_name] += len(items)
        logger.info("[TruthLens] %s general/%s -> %s articles", provider_name, region, len(items))
        return items, 0
    except Exception as exc:
        logger.warning("[TruthLens] %s general/%s failed: %s", provider_name, region, exc)
        return [], 1


def _fetch_priority_articles(
    provider_module,
    region: str,
    provider_counts: Counter,
    priority_counter: Counter,
) -> tuple[list[dict], int]:
    settings = get_settings()
    provider_name = getattr(provider_module, "PROVIDER_NAME", provider_module.__name__)
    items = []
    failures = 0

    for bundle in get_priority_topics(region):
        try:
            fetched = provider_module.fetch_priority(
                FetchRequest(
                    region=region,
                    mode="priority",
                    limit=settings.priority_feed_limit,
                    category=bundle.category,
                    query=bundle.label,
                    topic_bundle=bundle,
                )
            )
            items.extend(fetched)
            provider_counts[provider_name] += len(fetched)
            priority_counter[bundle.label] += len(fetched)
            logger.info(
                "[TruthLens] %s priority/%s/%s -> %s articles",
                provider_name,
                region,
                bundle.slug,
                len(fetched),
            )
        except Exception as exc:
            failures += 1
            logger.warning(
                "[TruthLens] %s priority/%s/%s failed: %s",
                provider_name,
                region,
                bundle.slug,
                exc,
            )

    return items, failures


def _collect_trend_signals() -> tuple[list[dict], int]:
    signals = []
    failures = 0

    for provider_module in TREND_MONITOR_PROVIDERS:
        provider_name = getattr(provider_module, "PROVIDER_NAME", provider_module.__name__)
        for region in ("ma", "world"):
            try:
                fetched = provider_module.fetch_trend_signals(region, get_priority_topics(region))
                signals.extend(fetched)
                logger.info("[TruthLens] %s trend/%s -> %s signals", provider_name, region, len(fetched))
            except Exception as exc:
                failures += 1
                logger.warning("[TruthLens] %s trend/%s failed: %s", provider_name, region, exc)

    return signals, failures


def run_ingestion_pipeline(batch_label: str) -> dict:
    started_at = datetime.now(timezone.utc).isoformat()
    provider_counts = Counter()
    priority_topic_counter = Counter()
    all_items = []
    failed_source_count = 0

    for region in ("ma", "world"):
        for provider_module in GENERAL_FEED_PROVIDERS:
            items, failed = _fetch_general_articles(provider_module, region, provider_counts)
            all_items.extend(items)
            failed_source_count += failed

        for provider_module in PRIORITY_FEED_PROVIDERS:
            items, failed = _fetch_priority_articles(
                provider_module,
                region,
                provider_counts,
                priority_topic_counter,
            )
            all_items.extend(items)
            failed_source_count += failed

    trend_signals, trend_failures = _collect_trend_signals()
    failed_source_count += trend_failures

    deduped_items, duplicate_stats = dedupe_articles(all_items)
    ranked_items = apply_ranking(deduped_items, trend_signals)
    trending_topics, trend_provider_summary = build_trend_intelligence(ranked_items) if ranked_items else ([], {})

    logger.info(
        "[TruthLens] provider counts=%s priority_topics=%s duplicates=%s trend_providers=%s",
        dict(provider_counts),
        dict(priority_topic_counter),
        duplicate_stats,
        trend_provider_summary,
    )

    conn = get_connection()
    cursor = conn.cursor()

    inserted_count, duplicate_count = upsert_news_items(cursor, ranked_items, batch_label)
    pruned_count = prune_old_news(cursor, get_settings().news_history_retention_days)

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
        "provider_counts": dict(provider_counts),
        "priority_topic_count": dict(priority_topic_counter),
        "url_duplicates_removed": duplicate_stats["url_duplicates_removed"],
        "title_duplicates_removed": duplicate_stats["title_duplicates_removed"],
        "pruned_count": pruned_count,
        "trend_provider_summary": trend_provider_summary,
    }
