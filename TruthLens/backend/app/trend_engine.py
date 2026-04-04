from collections import defaultdict
import json
import logging

from app.trend_providers import SOCIAL_TREND_PROVIDERS
from app.trend_providers.common import TrendProviderResult
from app.trend_providers.news_trend_provider import collect_trends as collect_news_trends


logger = logging.getLogger("truthlens.trends")

PLATFORM_WEIGHTS = {
    "x": 1.0,
    "reddit": 0.82,
    "instagram": 0.7,
    "tiktok": 0.74,
    "news": 0.78,
}


def build_trend_intelligence(articles: list[dict]) -> tuple[list[dict], dict]:
    provider_results = []
    aggregated = []

    for region in ("ma", "world"):
        news_result = collect_news_trends(region, articles)
        provider_results.append(news_result)
        aggregated.extend(news_result.signals)

        for provider_module in SOCIAL_TREND_PROVIDERS:
            try:
                result = provider_module.collect_trends(region)
            except Exception as exc:
                result = TrendProviderResult(
                    provider_name=getattr(provider_module, "PROVIDER_NAME", provider_module.__name__),
                    status="error",
                    signals=[],
                    note=str(exc),
                )

            provider_results.append(result)
            aggregated.extend(result.signals)

    grouped = defaultdict(list)
    for signal in aggregated:
        grouped[(signal.region, signal.normalized_topic)].append(signal)

    trend_records = []
    for (region, normalized_topic), signals in grouped.items():
        social_signals = [signal for signal in signals if signal.signal_type == "social"]
        news_signals = [signal for signal in signals if signal.signal_type == "news"]
        display_signal = max(signals, key=lambda signal: signal.score)

        source_signal_labels = [signal.provider_name for signal in news_signals]
        platform_signal_labels = [signal.platform for signal in social_signals]

        related_articles_count = max(
            [signal.related_articles_count for signal in signals],
            default=0,
        )
        recency_score = max([signal.recency_score for signal in signals], default=0.0)
        social_score = sum(signal.score * PLATFORM_WEIGHTS.get(signal.platform, 0.7) for signal in social_signals)
        news_score = sum(signal.score * PLATFORM_WEIGHTS.get(signal.platform, 0.78) for signal in news_signals)
        verification_score = min(
            100.0,
            sum(signal.verification_score for signal in news_signals) + min(24.0, len(source_signal_labels) * 6.0),
        )
        virality_score = min(
            100.0,
            social_score + news_score * 0.55 + related_articles_count * 3.0 + recency_score * 2.4,
        )
        verification_gap_score = max(0.0, round(virality_score - verification_score, 1))
        freshness_label = (
            "surging" if recency_score >= 8 else "fresh" if recency_score >= 5 else "active"
        )
        confidence_note = build_confidence_note(source_signal_labels, platform_signal_labels)
        verification_status = build_verification_status(verification_score, verification_gap_score)

        trend_records.append(
            {
                "topic": display_signal.title,
                "title": display_signal.title,
                "normalized_topic": normalized_topic,
                "region": region,
                "intensity": min(100, int(virality_score)),
                "article_count": related_articles_count,
                "related_articles_count": related_articles_count,
                "freshness": freshness_label,
                "freshness_label": freshness_label,
                "credibility_warning": verification_gap_score >= 18,
                "source_signals": json.dumps(sorted(set(source_signal_labels))),
                "platform_signals": json.dumps(sorted(set(platform_signal_labels))),
                "recency_score": round(recency_score, 1),
                "virality_score": round(virality_score, 1),
                "verification_score": round(verification_score, 1),
                "verification_gap_score": verification_gap_score,
                "confidence_note": confidence_note,
                "platform": display_signal.platform,
                "media_type": display_signal.media_type,
                "thumbnail_url": display_signal.thumbnail_url,
                "source_url": display_signal.source_url,
                "verification_status": verification_status,
            }
        )

    trend_records.sort(
        key=lambda item: (item["virality_score"], item["related_articles_count"], item["recency_score"]),
        reverse=True,
    )

    provider_summary = {
        result.provider_name: {"status": result.status, "signal_count": len(result.signals), "note": result.note}
        for result in provider_results
    }
    logger.info("[TruthLens Trends] provider summary=%s", provider_summary)

    return trend_records[:16], provider_summary


def build_confidence_note(source_signals: list[str], platform_signals: list[str]) -> str:
    if source_signals and platform_signals:
        return "Hybrid confidence: this trend is reinforced by both news coverage and social activity."
    if source_signals:
        return "News-led confidence: this trend is supported mainly by clustered news coverage."
    if platform_signals:
        return "Social-led signal: this trend is rising on social platforms and should be verified carefully."
    return "Limited confidence: only weak signals are currently available."


def build_verification_status(verification_score: float, verification_gap_score: float) -> str:
    if verification_gap_score >= 25:
        return "suspicious signals"
    if verification_score >= 70:
        return "supported by stronger sources"
    if verification_score >= 42:
        return "needs context"
    return "unverified"
