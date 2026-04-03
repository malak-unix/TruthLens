from urllib.parse import urlparse


SOURCE_REGISTRY = [
    {
        "name": "MAP News",
        "domain": "mapnews.ma",
        "region": "ma",
        "source_type": "editorial",
        "trust_level": "high",
        "language": "fr",
    },
    {
        "name": "Le Matin",
        "domain": "lematin.ma",
        "region": "ma",
        "source_type": "editorial",
        "trust_level": "high",
        "language": "fr",
    },
    {
        "name": "Hespress",
        "domain": "hespress.com",
        "region": "ma",
        "source_type": "editorial",
        "trust_level": "medium",
        "language": "ar",
    },
    {
        "name": "Morocco World News",
        "domain": "moroccoworldnews.com",
        "region": "ma",
        "source_type": "editorial",
        "trust_level": "medium",
        "language": "en",
    },
    {
        "name": "Reuters",
        "domain": "reuters.com",
        "region": "world",
        "source_type": "editorial",
        "trust_level": "high",
        "language": "en",
    },
    {
        "name": "Associated Press",
        "domain": "apnews.com",
        "region": "world",
        "source_type": "editorial",
        "trust_level": "high",
        "language": "en",
    },
    {
        "name": "BBC",
        "domain": "bbc.com",
        "region": "world",
        "source_type": "editorial",
        "trust_level": "high",
        "language": "en",
    },
    {
        "name": "CNN",
        "domain": "cnn.com",
        "region": "world",
        "source_type": "editorial",
        "trust_level": "medium",
        "language": "en",
    },
]


MOROCCO_RSS_SOURCES = [
    {
        "name": "Morocco World News",
        "url": "https://www.moroccoworldnews.com/feed",
        "region": "ma",
        "category": "International",
        "trust_level": "medium",
        "source_type": "editorial",
        "language": "en",
    },
]

WORLD_RSS_SOURCES = [
    {
        "name": "CNN World",
        "url": "http://rss.cnn.com/rss/edition_world.rss",
        "region": "world",
        "category": "International",
        "trust_level": "medium",
        "source_type": "editorial",
        "language": "en",
    },
    {
        "name": "CNN Business",
        "url": "http://rss.cnn.com/rss/edition_business.rss",
        "region": "world",
        "category": "Economy",
        "trust_level": "medium",
        "source_type": "editorial",
        "language": "en",
    },
    {
        "name": "CNN Technology",
        "url": "http://rss.cnn.com/rss/edition_technology.rss",
        "region": "world",
        "category": "Technology",
        "trust_level": "medium",
        "source_type": "editorial",
        "language": "en",
    },
]


def normalize_domain(value: str) -> str:
    if not value:
        return ""

    parsed = urlparse(value if "://" in value else f"https://{value}")
    domain = parsed.netloc.lower().replace("www.", "")
    return domain


def get_source_profile(url: str = "", source_name: str = "") -> dict:
    domain = normalize_domain(url)
    lowered_name = (source_name or "").strip().lower()

    for item in SOURCE_REGISTRY:
        if item["domain"] == domain:
            return item

    for item in SOURCE_REGISTRY:
        if lowered_name and lowered_name == item["name"].lower():
            return item

    region = "ma" if any(token in domain for token in ["morocco", ".ma"]) else "world"

    return {
        "name": source_name or domain or "Unknown source",
        "domain": domain,
        "region": region,
        "source_type": "discovery",
        "trust_level": "unknown",
        "language": "unknown",
    }