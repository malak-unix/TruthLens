import re
from urllib.parse import urlparse

from app.content_extractor import extract_article_from_url
from app.database import get_recent_articles_for_corroboration
from app.source_registry import SOURCE_REGISTRY, get_source_profile


SENSATIONAL_PATTERNS = [
    r"\bshocking\b",
    r"\bsecret\b",
    r"\bcover[- ]?up\b",
    r"\bscandal\b",
    r"\burgent\b",
    r"\bincroyable\b",
    r"\bchoc\b",
    r"\bscandale\b",
    r"\bcomplot\b",
    r"\bviral\b",
    r"\bbreaking\b",
    r"\bexclusive\b",
    r"\bmiracle\b",
    r"\bpartagez\b",
    r"\bshare\b",
    r"\byou won['’]t believe\b",
    r"\brevealed\b",
    r"\bclick here\b",
    r"\bmust see\b",
]

ATTRIBUTION_PATTERNS = [
    r"\baccording to\b",
    r"\bconfirmed by\b",
    r"\bsaid\b",
    r"\bannounced\b",
    r"\bofficial statement\b",
    r"\bministry of\b",
    r"\bpolice said\b",
    r"\bgovernment said\b",
    r"\bspokesperson\b",
    r"\breported\b",
]

STOPWORDS = {
    "about",
    "after",
    "against",
    "also",
    "amid",
    "because",
    "been",
    "before",
    "being",
    "between",
    "claim",
    "could",
    "from",
    "into",
    "more",
    "news",
    "over",
    "report",
    "says",
    "said",
    "that",
    "their",
    "them",
    "there",
    "these",
    "they",
    "this",
    "through",
    "today",
    "video",
    "what",
    "when",
    "where",
    "with",
    "would",
}


def clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def detect_input_type(text: str, url: str) -> str:
    if url:
        return "url"
    normalized = (text or "").strip().lower()
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return "url"
    return "text"


def safe_domain_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def tokenize_for_match(*values: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9']+", " ".join(values).lower())
    return {
        token
        for token in tokens
        if len(token) >= 4 and token not in STOPWORDS and not token.isdigit()
    }


def score_sensational_language(text: str) -> tuple[int, list[str]]:
    penalty = 0
    signals = []

    for pattern in SENSATIONAL_PATTERNS:
        match = re.search(pattern, text.lower())
        if match:
            penalty += 6
            signals.append(f"Manipulative wording detected: {match.group(0)}")

    if "!!" in text or text.count("!") >= 3:
        penalty += 6
        signals.append("Excessive punctuation in the headline or claim")

    uppercase_words = [word for word in text.split() if len(word) > 4 and word.isupper()]
    if len(uppercase_words) >= 3:
        penalty += 5
        signals.append("Headline relies heavily on shouty uppercase wording")

    return penalty, signals


def score_attribution(text: str) -> tuple[int, list[str]]:
    matches = []
    lowered = text.lower()

    for pattern in ATTRIBUTION_PATTERNS:
        match = re.search(pattern, lowered)
        if match:
            matches.append(match.group(0))

    named_sources = []
    for item in SOURCE_REGISTRY:
        names = [item["source_name"].lower(), *item.get("aliases", [])]
        if any(name in lowered for name in names):
            named_sources.append(item["source_name"])

    delta = 0
    signals = []

    if len(matches) >= 3:
        delta += 16
        signals.append("Multiple attribution markers were found in the content")
    elif len(matches) == 2:
        delta += 11
        signals.append("Two attribution markers were found in the content")
    elif len(matches) == 1:
        delta += 5
        signals.append(f"Attribution marker found: {matches[0]}")
    else:
        delta -= 6
        signals.append("Few explicit attribution markers were found")

    if named_sources:
        delta += min(8, len(named_sources) * 3)
        signals.append("Named sources mentioned: " + ", ".join(named_sources[:3]))

    return delta, signals


def score_context_quality(text: str) -> tuple[int, list[str]]:
    words = text.split()
    count = len(words)

    if count < 18:
        return -16, ["Very little context is available in the text"]
    if count < 45:
        return -4, ["Context is limited and should be checked against fuller reporting"]
    if count < 120:
        return 8, ["The article has enough detail for a first-pass review"]
    return 14, ["The article provides substantial contextual detail"]


def score_metadata_quality(
    *,
    title: str,
    description: str,
    author: str,
    published_at: str,
    url: str,
    input_type: str,
) -> tuple[int, list[str]]:
    score = 0
    signals = []

    if title:
        score += 4
    else:
        signals.append("Missing clear title or headline")

    if description and len(description.split()) >= 10:
        score += 6
    elif input_type == "url":
        signals.append("Limited article summary or metadata description")

    if input_type == "url":
        if author:
            score += 8
            signals.append("A byline or author name was found")
        else:
            score -= 4
            signals.append("No clear author/byline was found")

        if published_at:
            score += 6
            signals.append("A publication date was found")
        else:
            score -= 3
            signals.append("No clear publication date was found")

        if url.startswith("https://"):
            score += 2
        else:
            score -= 2
            signals.append("The URL is not using HTTPS")

    return score, signals


def evaluate_source_score(profile: dict) -> tuple[int, list[str]]:
    score = float(profile.get("base_reliability_score", 54))
    signals = []
    risk_tier = profile.get("risk_tier", "moderate")

    if risk_tier == "high":
        score -= 18
        signals.append("The publisher is in a high-risk registry tier")
    elif risk_tier == "moderate":
        score -= 3

    if profile.get("corrections_policy_known"):
        score += 4
        signals.append("The publisher has a visible corrections process")
    if profile.get("ownership_known"):
        score += 3
        signals.append("Ownership information is identifiable")
    if profile.get("byline_practice_known"):
        score += 3
        signals.append("The outlet usually uses named bylines")
    if profile.get("fact_checker_flag"):
        score += 4
        signals.append("The publisher is a fact-checking organization")

    if profile.get("trust_level") == "unknown":
        signals.append("The source is not yet in the structured registry, so the source prior stays neutral")
    else:
        signals.append(
            f"Registry baseline for {profile.get('source_name', 'this outlet')}: "
            f"{profile.get('base_reliability_score', 54)}/100"
        )

    return clamp_score(score), signals


def evaluate_article_score(
    *,
    title: str,
    description: str,
    text: str,
    author: str,
    published_at: str,
    url: str,
    input_type: str,
) -> tuple[int, list[str]]:
    score = 55.0 if input_type == "url" else 52.0
    signals = []

    headline_penalty, headline_signals = score_sensational_language(f"{title}. {description}")
    score -= headline_penalty
    signals.extend(headline_signals)

    if headline_penalty == 0 and title:
        score += 6
        signals.append("The headline is relatively restrained and non-clickbait")

    attribution_delta, attribution_signals = score_attribution(f"{title}. {description}. {text}")
    score += attribution_delta
    signals.extend(attribution_signals)

    context_delta, context_signals = score_context_quality(text or f"{title}. {description}")
    score += context_delta
    signals.extend(context_signals)

    metadata_delta, metadata_signals = score_metadata_quality(
        title=title,
        description=description,
        author=author,
        published_at=published_at,
        url=url,
        input_type=input_type,
    )
    score += metadata_delta
    signals.extend(metadata_signals)

    return clamp_score(score), signals


def evaluate_corroboration_score(
    *,
    title: str,
    description: str,
    text: str,
    source_profile: dict,
    source_domain: str,
) -> tuple[int, list[str], int]:
    score = 50.0
    signals = []
    reliable_matches = {}
    keywords = tokenize_for_match(title, description, text)

    if len(keywords) >= 3:
        for candidate in get_recent_articles_for_corroboration(limit=80):
            candidate_domain = (candidate.get("source_domain") or "").lower()
            if source_domain and candidate_domain == source_domain:
                continue

            candidate_tokens = tokenize_for_match(candidate.get("title", ""), candidate.get("description", ""))
            if not candidate_tokens:
                continue

            overlap = len(keywords & candidate_tokens)
            similarity = overlap / max(1, len(keywords | candidate_tokens))

            if overlap >= 3 or similarity >= 0.2:
                if candidate.get("source_trust_level") in {"high", "medium"}:
                    reliable_matches[candidate_domain or candidate.get("source_name", "unknown")] = candidate

    corroboration_count = len(reliable_matches)

    if corroboration_count >= 3:
        score += 34
        signals.append("Multiple monitored outlets report overlapping details")
    elif corroboration_count == 2:
        score += 24
        signals.append("Two monitored outlets report overlapping details")
    elif corroboration_count == 1:
        score += 12
        signals.append("One monitored outlet reports overlapping details")
    else:
        score -= 2
        signals.append("No strong corroboration was found in the current monitoring set")

    if source_profile.get("fact_checker_flag"):
        score += 6
        signals.append("The source specializes in fact-checking and evidence-based review")

    if source_profile.get("risk_tier") == "high" and corroboration_count == 0:
        score -= 20
        signals.append("A high-risk source without corroboration needs strong manual review")

    return clamp_score(score), signals, corroboration_count


def label_from_score(score: int) -> str:
    if score >= 80:
        return "Reliable"
    if score >= 65:
        return "Needs Context"
    if score >= 48:
        return "Unverified"
    if score >= 32:
        return "Suspicious"
    return "High Risk"


def build_verification_status(
    corroboration_score: int,
    corroboration_count: int,
    source_profile: dict,
) -> str:
    if corroboration_score >= 78 and corroboration_count >= 2:
        return "Corroborated by multiple monitored sources"
    if corroboration_score >= 62:
        return "Partially corroborated"
    if source_profile.get("risk_tier") == "high" and corroboration_count == 0:
        return "Unsupported from a high-risk source"
    return "Awaiting stronger corroboration"


def build_confidence_note(
    *,
    extracted_ok: bool,
    source_score: int,
    article_score: int,
    corroboration_score: int,
) -> str:
    if extracted_ok and source_score >= 78 and article_score >= 70 and corroboration_score >= 68:
        return "Higher confidence in the estimate: source, article quality, and corroboration are all supportive. This is still not absolute truth."
    if extracted_ok and (article_score >= 65 or corroboration_score >= 60):
        return "Moderate confidence in the estimate: some structured signals are supportive, but more verification may still be needed."
    return "Limited confidence in the estimate: this is an explainable credibility aid, not a truth verdict."


def build_verification_tips(
    *,
    source_profile: dict,
    source_score: int,
    article_score: int,
    corroboration_score: int,
    domain: str,
) -> list[str]:
    tips = []

    if source_score < 60:
        tips.append("Check the publisher's ownership, editorial page, and corrections policy.")
    if article_score < 60:
        tips.append("Verify the author, date, and original evidence cited in the article.")
    if corroboration_score < 62:
        tips.append("Look for at least two independent reliable sources reporting the same claim.")
    if source_profile.get("fact_checker_flag"):
        tips.append("Review the evidence and source links cited by the fact-checking organization.")
    if domain:
        tips.append(f"Review whether {domain} clearly identifies authorship and sourcing.")
    tips.append("Treat the result as a verification aid, not as a final truth judgment.")

    deduped = []
    for item in tips:
        if item not in deduped:
            deduped.append(item)
    return deduped[:4]


def dedupe_signals(values: list[str], limit: int = 8) -> list[str]:
    output = []
    for item in values:
        if item and item not in output:
            output.append(item)
        if len(output) >= limit:
            break
    return output


def analyze_payload(
    text: str | None = None,
    url: str | None = None,
    source_name: str = "",
    article_metadata: dict | None = None,
) -> dict:
    input_type = detect_input_type(text or "", url or "")
    extracted = None
    metadata = article_metadata or {}

    effective_url = (url or metadata.get("url") or "").strip()
    effective_title = normalize_text(metadata.get("title", ""))
    effective_description = normalize_text(
        metadata.get("description", "") or metadata.get("meta_description", "")
    )
    effective_text = normalize_text(metadata.get("text", "") or text or "")
    effective_author = normalize_text(metadata.get("author", ""))
    effective_published_at = normalize_text(metadata.get("published_at", ""))
    extracted_ok = bool(metadata)

    if input_type == "url" and not metadata:
        target_url = effective_url or (text or "").strip()
        extracted = extract_article_from_url(target_url)
        effective_url = target_url
        effective_title = normalize_text(extracted.get("title", ""))
        effective_description = normalize_text(extracted.get("meta_description", ""))
        effective_text = normalize_text(extracted.get("text", ""))
        effective_author = normalize_text(extracted.get("author", ""))
        effective_published_at = normalize_text(extracted.get("published_at", ""))
        extracted_ok = extracted.get("status") == "ok"
        if not source_name:
            source_name = extracted.get("domain", "")

    if not effective_text:
        effective_text = normalize_text(f"{effective_title}. {effective_description}")

    if not effective_text and not effective_url:
        empty_profile = get_source_profile()
        return {
            "credibility_score": 0,
            "credibility_label": "No Input",
            "final_score": 0,
            "final_label": "No Input",
            "source_score": 0,
            "article_score": 0,
            "corroboration_score": 0,
            "verification_status": "No content provided",
            "explanation": "No content was provided for analysis.",
            "risk_signals": ["Empty input"],
            "confidence_note": "No analysis possible.",
            "verification_tips": ["Provide a text claim or a URL."],
            "domain_analysis": {
                "domain": "",
                "trust_level": empty_profile.get("trust_level", "unknown"),
                "source_type": empty_profile.get("source_type", "unknown"),
                "region": empty_profile.get("region", "unknown"),
            },
            "source_profile": empty_profile,
            "extracted_preview": {"title": "", "meta_description": ""},
        }

    domain = safe_domain_from_url(effective_url)
    profile = get_source_profile(url=effective_url or domain, source_name=source_name)

    source_score, source_signals = evaluate_source_score(profile)
    article_score, article_signals = evaluate_article_score(
        title=effective_title,
        description=effective_description,
        text=effective_text,
        author=effective_author,
        published_at=effective_published_at,
        url=effective_url,
        input_type=input_type,
    )
    corroboration_score, corroboration_signals, corroboration_count = evaluate_corroboration_score(
        title=effective_title,
        description=effective_description,
        text=effective_text,
        source_profile=profile,
        source_domain=domain,
    )

    if input_type == "url" and extracted and extracted.get("status") != "ok":
        article_score = clamp_score(article_score - 8)
        article_signals.append("The article page could not be fully extracted")

    final_score = clamp_score(
        (source_score * 30 + article_score * 50 + corroboration_score * 20) / 100
    )

    if corroboration_score < 60 and final_score >= 80:
        final_score = 79
        corroboration_signals.append("Strong source and article signals are present, but corroboration is still limited")

    final_label = label_from_score(final_score)
    verification_status = build_verification_status(
        corroboration_score=corroboration_score,
        corroboration_count=corroboration_count,
        source_profile=profile,
    )

    explanation = (
        "This is an explainable credibility estimate, not a truth verdict. "
        f"Source score: {source_score}/100 for {profile.get('source_name', 'the publisher')}. "
        f"Article score: {article_score}/100 based on attribution, metadata, wording, and context. "
        f"Corroboration score: {corroboration_score}/100 from the current monitored reporting set. "
        f"Final score: {final_score}/100, labelled {final_label}. "
        f"Verification status: {verification_status}."
    )

    risk_signals = dedupe_signals(source_signals + article_signals + corroboration_signals)

    return {
        "credibility_score": final_score,
        "credibility_label": final_label,
        "final_score": final_score,
        "final_label": final_label,
        "source_score": source_score,
        "article_score": article_score,
        "corroboration_score": corroboration_score,
        "verification_status": verification_status,
        "explanation": explanation,
        "risk_signals": risk_signals,
        "confidence_note": build_confidence_note(
            extracted_ok=extracted_ok,
            source_score=source_score,
            article_score=article_score,
            corroboration_score=corroboration_score,
        ),
        "verification_tips": build_verification_tips(
            source_profile=profile,
            source_score=source_score,
            article_score=article_score,
            corroboration_score=corroboration_score,
            domain=domain,
        ),
        "domain_analysis": {
            "domain": domain,
            "trust_level": profile.get("trust_level", "unknown"),
            "source_type": profile.get("source_type", "unknown"),
            "region": profile.get("region", "unknown"),
        },
        "source_profile": profile,
        "extracted_preview": {
            "title": extracted.get("title", "") if extracted else effective_title,
            "meta_description": extracted.get("meta_description", "") if extracted else effective_description,
        },
    }


def analyze_text_content(content: str):
    return analyze_payload(text=content)
