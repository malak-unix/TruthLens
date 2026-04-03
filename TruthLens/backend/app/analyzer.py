import re
from urllib.parse import urlparse

from app.content_extractor import extract_article_from_url
from app.source_registry import get_source_profile


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
    r"\breuters reported\b",
    r"\bbbc reported\b",
    r"\bpolice said\b",
]

TRUST_LEVEL_SCORES = {
    "high": 18,
    "medium": 8,
    "low": -6,
    "unknown": -2,
}

SUSPICIOUS_DOMAIN_HINTS = [
    "blogspot",
    "telegram",
    "rumor",
    "viral",
    "anon",
    "clickbait",
]


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


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


def score_sensational_language(text: str) -> tuple[int, list[str]]:
    penalty = 0
    signals = []

    for pattern in SENSATIONAL_PATTERNS:
        match = re.search(pattern, text)
        if match:
            penalty += 8
            signals.append(f"Sensational cue detected: {match.group(0)}")

    return penalty, signals


def score_attribution(text: str) -> tuple[int, list[str]]:
    matches = []
    for pattern in ATTRIBUTION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            matches.append(match.group(0))

    if len(matches) >= 2:
        return 12, [f"Attribution markers detected: {', '.join(matches[:2])}"]
    if len(matches) == 1:
        return 5, [f"Attribution marker detected: {matches[0]}"]
    return -10, ["No strong attribution marker detected"]


def score_context_quality(text: str) -> tuple[int, list[str]]:
    words = text.split()
    count = len(words)

    if count < 12:
        return -20, ["Very little context available"]
    if count < 35:
        return -8, ["Limited contextual detail"]
    if count < 90:
        return 4, ["Enough context for a first-pass review"]
    return 8, ["Rich contextual detail available"]


def score_source_profile(domain: str, source_name: str) -> tuple[int, list[str], dict]:
    profile = get_source_profile(url=domain, source_name=source_name)

    trust_level = profile.get("trust_level", "unknown")
    delta = TRUST_LEVEL_SCORES.get(trust_level, -2)

    signals = [f"Source trust level evaluated as: {trust_level}"]

    if any(token in domain for token in SUSPICIOUS_DOMAIN_HINTS):
        delta -= 15
        signals.append("Suspicious domain pattern detected")

    return delta, signals, profile


def score_url_quality(url: str) -> tuple[int, list[str]]:
    signals = []
    delta = 0

    if not url:
        return 0, signals

    if url.startswith("https://"):
        delta += 2
        signals.append("HTTPS URL detected")
    else:
        delta -= 2
        signals.append("Non-HTTPS URL detected")

    if "utm_" in url or "fbclid=" in url:
        delta -= 5
        signals.append("Tracking-heavy URL detected")

    return delta, signals


def label_from_score(score: int) -> str:
    if score >= 82:
        return "Reliable"
    if score >= 62:
        return "Needs Context"
    if score >= 40:
        return "Unverified"
    if score >= 20:
        return "Suspicious"
    return "High Risk"


def build_confidence_note(text_length: int, source_trust: str, extracted_ok: bool) -> str:
    if extracted_ok and source_trust in {"high", "medium"} and text_length > 35:
        return "Moderate confidence: source and content signals were available."
    if extracted_ok:
        return "Limited confidence: some content was extracted, but corroboration is still needed."
    return "Low confidence: limited content was available, so this is only an early credibility estimate."


def build_verification_tips(label: str, domain: str) -> list[str]:
    tips = [
        "Check whether at least two independent sources report the same claim.",
        "Look for named institutions, officials, or original documents.",
    ]

    if domain:
        tips.append(f"Review the reputation and ownership of {domain}.")

    if label in {"Suspicious", "High Risk", "Unverified"}:
        tips.append("Treat the claim as unverified until confirmed by stronger sources.")

    return tips[:4]


def analyze_payload(text: str | None = None, url: str | None = None, source_name: str = "") -> dict:
    input_type = detect_input_type(text or "", url or "")
    extracted = None
    effective_text = normalize_text(text or "")
    effective_url = (url or "").strip()

    if input_type == "url":
        target_url = effective_url or (text or "").strip()
        extracted = extract_article_from_url(target_url)
        effective_url = target_url
        pieces = [
            extracted.get("title", ""),
            extracted.get("meta_description", ""),
            extracted.get("text", ""),
        ]
        effective_text = normalize_text(" ".join(piece for piece in pieces if piece))
        if not source_name:
            source_name = extracted.get("domain", "")

    if not effective_text and not effective_url:
        return {
            "credibility_score": 0,
            "credibility_label": "No Input",
            "explanation": "No content was provided for analysis.",
            "risk_signals": ["Empty input"],
            "confidence_note": "No analysis possible.",
            "verification_tips": ["Provide a text claim or a URL."],
            "domain_analysis": {
                "domain": "",
                "trust_level": "unknown",
                "source_type": "unknown",
                "region": "unknown",
            },
        }

    score = 50
    risk_signals = []

    sensational_penalty, sensational_signals = score_sensational_language(effective_text)
    score -= sensational_penalty
    risk_signals.extend(sensational_signals)

    attribution_delta, attribution_signals = score_attribution(effective_text)
    score += attribution_delta
    risk_signals.extend(attribution_signals)

    context_delta, context_signals = score_context_quality(effective_text)
    score += context_delta
    risk_signals.extend(context_signals)

    domain = safe_domain_from_url(effective_url)
    source_delta, source_signals, source_profile = score_source_profile(domain, source_name)
    score += source_delta
    risk_signals.extend(source_signals)

    url_delta, url_signals = score_url_quality(effective_url)
    score += url_delta
    risk_signals.extend(url_signals)

    if input_type == "url" and extracted and extracted.get("status") != "ok":
        score -= 10
        risk_signals.append("The article page could not be fully extracted")

    score = max(0, min(100, score))
    label = label_from_score(score)

    explanation_parts = [
        f"This {input_type} was evaluated with explainable credibility signals.",
        f"Final score: {score}/100.",
        f"Label: {label}.",
        f"Source trust: {source_profile.get('trust_level', 'unknown')}.",
    ]

    if risk_signals:
        explanation_parts.append("Main signals: " + ", ".join(risk_signals[:6]) + ".")

    confidence_note = build_confidence_note(
        text_length=len(effective_text.split()),
        source_trust=source_profile.get("trust_level", "unknown"),
        extracted_ok=bool(extracted and extracted.get("status") == "ok"),
    )

    return {
        "credibility_score": score,
        "credibility_label": label,
        "explanation": " ".join(explanation_parts),
        "risk_signals": risk_signals[:8],
        "confidence_note": confidence_note,
        "verification_tips": build_verification_tips(label, domain),
        "domain_analysis": {
            "domain": domain,
            "trust_level": source_profile.get("trust_level", "unknown"),
            "source_type": source_profile.get("source_type", "unknown"),
            "region": source_profile.get("region", "unknown"),
        },
        "extracted_preview": {
            "title": extracted.get("title", "") if extracted else "",
            "meta_description": extracted.get("meta_description", "") if extracted else "",
        },
    }


def analyze_text_content(content: str):
    return analyze_payload(text=content)