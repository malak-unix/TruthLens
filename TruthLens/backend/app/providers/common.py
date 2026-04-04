from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
import re

import requests

from app.analyzer import analyze_payload
from app.priority_topics import PriorityTopicBundle, bundle_match_score, match_priority_topics
from app.source_registry import get_source_profile


USER_AGENT = "TruthLens/1.0"
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}


@dataclass(frozen=True)
class FetchRequest:
    region: str
    mode: str
    limit: int
    category: str = "International"
    query: str = ""
    topic_bundle: Optional[PriorityTopicBundle] = None


def sanitize_text(value: str | None, fallback: str = "") -> str:
    text = unescape((value or "").strip())
    return " ".join(text.split()) or fallback


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


def canonicalize_url(value: str | None) -> str:
    raw = sanitize_text(value, "")
    if not raw:
        return ""

    parsed = urlparse(raw)
    query_items = [
        (key, item)
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
        if key not in TRACKING_PARAMS
    ]

    cleaned = parsed._replace(
        fragment="",
        query=urlencode(query_items, doseq=True),
        netloc=parsed.netloc.lower().replace("www.", ""),
    )
    return urlunparse(cleaned)


def normalize_image_url(value: str | None) -> str:
    raw = sanitize_text(value, "")
    if not raw:
        return ""

    if raw.startswith(("http://", "https://")):
        return raw

    return ""


def parse_timestamp(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()

    raw = value.strip()

    try:
        if raw.endswith("Z") and "T" in raw:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
        if "T" in raw and "+" in raw:
            return datetime.fromisoformat(raw).astimezone(timezone.utc).isoformat()
        if raw.endswith("Z") and len(raw) == 16:
            return datetime.strptime(raw, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        pass

    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def request_json(url: str, params: dict, timeout: int) -> dict | None:
    try:
        response = requests.get(
            url,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return None


def is_morocco_relevant(title: str, description: str, url: str, source_name: str) -> bool:
    haystack = f"{title} {description} {source_name} {url}".lower()
    terms = (
        "morocco",
        "moroccan",
        "rabat",
        "casablanca",
        "tangier",
        "marrakech",
        "agadir",
        "fes",
        ".ma",
    )
    return any(term in haystack for term in terms)


def detect_category(title: str, description: str, fallback: str = "International") -> str:
    haystack = f"{title} {description}".lower()
    rules = {
        "Politics": ("election", "minister", "parliament", "government", "president", "diplomacy"),
        "Economy": ("economy", "market", "trade", "inflation", "bank", "tariff", "tax"),
        "Technology": ("technology", "ai", "cyber", "chip", "software", "digital"),
        "Health": ("health", "hospital", "vaccine", "medical", "disease", "who"),
        "Sports": ("sport", "football", "soccer", "match", "league", "team"),
        "Society": ("school", "housing", "education", "community", "migration", "protest"),
        "International": (
            "war",
            "conflict",
            "ceasefire",
            "humanitarian",
            "missile",
            "strike",
            "crisis",
            "border",
        ),
    }

    for category, keywords in rules.items():
        if any(keyword in haystack for keyword in keywords):
            return category

    return fallback


def compute_completeness_score(title: str, description: str, source_name: str, published_at: str) -> float:
    score = 0.0
    if title:
        score += 3
    if description and len(description.split()) >= 10:
        score += 3
    if source_name:
        score += 2
    if published_at:
        score += 2
    return score


def normalize_article(
    *,
    provider_name: str,
    title: str,
    description: str,
    url: str,
    published_at: str,
    source_name: str,
    image_url: str = "",
    fallback_region: str,
    fallback_category: str,
    topic_bundle: Optional[PriorityTopicBundle] = None,
    trend_score: float = 0.0,
) -> dict | None:
    clean_url = canonicalize_url(url)
    if not clean_url:
        return None

    clean_title = sanitize_text(title, "Untitled article")
    clean_description = sanitize_text(strip_html(description), clean_title)
    clean_source = sanitize_text(source_name, provider_name)
    effective_published_at = parse_timestamp(published_at)

    profile = get_source_profile(url=clean_url, source_name=clean_source)
    region = profile.get("region", fallback_region)

    if fallback_region == "ma" or is_morocco_relevant(clean_title, clean_description, clean_url, clean_source):
        region = "ma"
    elif fallback_region:
        region = fallback_region

    category = detect_category(clean_title, clean_description, fallback_category)
    matched_topics = match_priority_topics(f"{clean_title} {clean_description}", region)

    if topic_bundle and topic_bundle not in matched_topics:
        matched_topics = [topic_bundle, *matched_topics]

    bundle_score = bundle_match_score(f"{clean_title} {clean_description}", topic_bundle) if topic_bundle else 0
    primary_topic = (
        topic_bundle
        if topic_bundle and bundle_score > 0
        else (matched_topics[0] if matched_topics else None)
    )
    priority_score = max(
        [topic.priority_weight for topic in matched_topics],
        default=0,
    )

    if primary_topic and primary_topic.priority_weight > priority_score:
        priority_score = primary_topic.priority_weight

    analysis = analyze_payload(
        text=f"{clean_title}. {clean_description}",
        url=clean_url,
        source_name=clean_source,
        article_metadata={
            "url": clean_url,
            "title": clean_title,
            "description": clean_description,
            "text": clean_description,
            "published_at": effective_published_at,
            "author": "",
        },
    )

    source_domain = urlparse(clean_url).netloc.lower().replace("www.", "")

    return {
        "title": clean_title,
        "source_name": clean_source,
        "published_at": effective_published_at,
        "country": region,
        "category": category,
        "url": clean_url,
        "image_url": normalize_image_url(image_url),
        "description": clean_description,
        "credibility_score": analysis["credibility_score"],
        "credibility_label": analysis["credibility_label"],
        "explanation": analysis["explanation"],
        "source_type": profile.get("source_type", "discovery"),
        "source_trust_level": profile.get("trust_level", "unknown"),
        "language": profile.get("language", "unknown"),
        "provider_name": provider_name,
        "source_domain": source_domain,
        "priority_topic": primary_topic.label if primary_topic else "",
        "priority_score": float(priority_score),
        "trend_score": float(trend_score),
        "coverage_score": 0.0,
        "ranking_score": 0.0,
        "dedupe_key": "",
        "is_priority": bool(primary_topic),
        "is_conflict": bool(primary_topic and primary_topic.conflict_related),
        "completeness_score": compute_completeness_score(
            clean_title,
            clean_description,
            clean_source,
            effective_published_at,
        ),
        "source_score": analysis.get("source_score"),
        "article_score": analysis.get("article_score"),
        "corroboration_score": analysis.get("corroboration_score"),
        "verification_status": analysis.get("verification_status"),
    }


def title_tokens(title: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9']+", (title or "").lower())
