from collections import Counter, defaultdict

from app.trend_providers.common import (
    GENERIC_TREND_TOKENS,
    TrendProviderResult,
    TrendSignal,
    display_title_from_topic,
    freshness_score_from_timestamp,
    normalize_topic,
)


PROVIDER_NAME = "News"

PHRASE_STOPWORDS = GENERIC_TREND_TOKENS | {
    "against",
    "calls",
    "says",
    "saying",
    "shows",
    "their",
    "these",
    "those",
    "very",
    "what",
}


def collect_trends(region: str, articles: list[dict]) -> TrendProviderResult:
    region_articles = [article for article in articles if article.get("country") == region]
    if not region_articles:
        return TrendProviderResult(
            provider_name=PROVIDER_NAME,
            status="unavailable",
            signals=[],
            note="No articles available to derive news-based trends.",
        )

    grouped = defaultdict(list)

    for article in region_articles:
        cluster_title, normalized = derive_topic_phrase(article)
        if not normalized:
            continue
        grouped[normalized].append((cluster_title, article))

    signals = []

    for normalized, entries in grouped.items():
        articles_for_topic = [article for _, article in entries]
        distinct_urls = {article["url"] for article in articles_for_topic}
        if len(distinct_urls) < 2 and not any(article.get("is_priority") for article in articles_for_topic):
            continue

        titles = Counter(title for title, _ in entries)
        display_title = titles.most_common(1)[0][0]
        related_articles_count = len(distinct_urls)
        avg_rank = sum(float(article.get("ranking_score", 0)) for article in articles_for_topic) / len(articles_for_topic)
        avg_verification = sum(float(article.get("credibility_score", 0)) for article in articles_for_topic) / len(articles_for_topic)
        latest = max(article.get("published_at", "") for article in articles_for_topic)

        signals.append(
            TrendSignal(
                title=display_title,
                normalized_topic=normalized,
                region=region,
                provider_name=PROVIDER_NAME,
                signal_type="news",
                score=min(100.0, related_articles_count * 12 + avg_rank * 0.35),
                volume=related_articles_count,
                recency_score=freshness_score_from_timestamp(latest),
                confidence=0.86,
                platform="news",
                related_articles_count=related_articles_count,
                verification_score=avg_verification / 10.0,
                note="Derived from clustered article coverage.",
            )
        )

    return TrendProviderResult(
        provider_name=PROVIDER_NAME,
        status="available",
        signals=sorted(signals, key=lambda item: item.score, reverse=True)[:12],
        note="News-based trend extraction completed.",
    )


def derive_topic_phrase(article: dict) -> tuple[str, str]:
    if article.get("priority_topic"):
        title = article["priority_topic"]
        return title, normalize_topic(title)

    title = (article.get("title") or "").replace("–", "-")
    main_segment = title.split(":")[0].split(" - ")[0].strip() or title
    tokens = [token for token in normalize_topic(main_segment).split("-") if token]

    if len(tokens) >= 2:
        phrase = " ".join(tokens[:4])
        return display_title_from_topic(phrase), normalize_topic(phrase)

    original_tokens = [
        token.lower()
        for token in main_segment.replace("'", " ").split()
        if len(token) > 3
    ]
    filtered = [token for token in original_tokens if token not in PHRASE_STOPWORDS]
    if len(filtered) >= 2:
        phrase = " ".join(filtered[:4])
        return display_title_from_topic(phrase), normalize_topic(phrase)

    return "", ""
