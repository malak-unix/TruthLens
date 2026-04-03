import re
from urllib.parse import urlparse

SENSATIONAL_PATTERNS = [
    r"\bshocking\b",
    r"\bsecret\b",
    r"\bcover-up\b",
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
]

TRUSTED_PHRASES = [
    "official statement",
    "confirmed by",
    "according to",
    "press release",
    "ministry of",
    "parliament",
    "government statement",
]

TRUSTED_DOMAINS = [
    "gov",
    "who.int",
    "un.org",
    "reuters.com",
    "bbc.com",
    "bbc.co.uk",
    "apnews.com",
    "theguardian.com",
    "guardian.co.uk",
    "cnn.com",
    "lematin.ma",
    "mapnews.ma",
]

LOW_CONFIDENCE_DOMAINS = [
    "nypost.com",
    "says.com",
    "insidethemagic.net",
    "disneyfoodblog.com",
    "odditycentral.com",
    "joefavorito.com",
]

SUSPICIOUS_DOMAINS = [
    "blogspot",
    "telegram",
    "rumor",
    "viral",
    "unknown",
]

BALANCED_TERMS = ["according to", "said", "told", "announced", "confirmed"]


def normalize_content(content: str) -> str:
    return re.sub(r"\s+", " ", content.strip().lower())


def detect_input_type(content: str) -> str:
    if content.startswith("http://") or content.startswith("https://"):
        return "url"
    return "text"


def extract_domain(content: str) -> str:
    parsed = urlparse(content)
    return parsed.netloc.lower().replace("www.", "")


def score_sensational_language(text: str):
    penalty = 0
    signals = []

    for pattern in SENSATIONAL_PATTERNS:
        match = re.search(pattern, text)
        if match:
            penalty += 10
            signals.append(f"Sensational cue detected: {match.group(0)}")

    return penalty, signals


def score_trusted_signals(text: str):
    bonus = 0
    found = 0
    signals = []

    for phrase in TRUSTED_PHRASES:
        if phrase in text:
            bonus += 7
            found += 1
            signals.append(f"Credibility cue detected: {phrase}")

    return bonus, found, signals


def score_url_reputation(text: str):
    delta = 0
    signals = []
    domain = extract_domain(text)

    for trusted_domain in TRUSTED_DOMAINS:
        if trusted_domain in domain:
            delta += 15
            signals.append(f"Trusted domain detected: {trusted_domain}")
            break

    for suspicious_domain in SUSPICIOUS_DOMAINS:
        if suspicious_domain in domain:
            delta -= 20
            signals.append(f"Potentially weak source detected: {suspicious_domain}")
            break

    for low_confidence_domain in LOW_CONFIDENCE_DOMAINS:
        if low_confidence_domain in domain:
            delta -= 12
            signals.append(f"Low-confidence source detected: {low_confidence_domain}")
            break

    if domain and text.startswith("https://"):
        delta += 2
        signals.append("HTTPS source detected")

    if "utm_" in text or "fbclid=" in text or "preview=" in text:
        delta -= 8
        signals.append("Tracking-heavy URL detected")

    return delta, signals


def score_length_and_context(text: str):
    words = text.split()
    signals = []
    delta = 0

    if len(words) < 8:
        delta -= 24
        signals.append("Very short content, almost no context")
    elif len(words) < 18:
        delta -= 12
        signals.append("Short content, limited context")
    elif len(words) > 35:
        delta += 4
        signals.append("Enough detail for contextual review")

    return delta, signals


def score_source_presence(text: str):
    strong_source_patterns = [
        r"\baccording to\b",
        r"\bconfirmed by\b",
        r"\bofficial statement\b",
        r"\bgovernment statement\b",
        r"\bministry of\b",
        r"\bpolice said\b",
        r"\breuters reported\b",
        r"\bbbc reported\b",
    ]

    found = []
    for pattern in strong_source_patterns:
        match = re.search(pattern, text)
        if match:
            found.append(match.group(0))

    if found:
        return 10, [f"Source cue detected: {item}" for item in found[:2]]

    return -12, ["No strong source attribution detected"]


def score_balance_markers(text: str):
    found = [term for term in BALANCED_TERMS if term in text]
    if len(found) >= 2:
        return 6, ["Balanced reporting markers detected"]
    if len(found) == 1:
        return 2, [f"Reporting marker detected: {found[0]}"]
    return 0, []


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


def build_explanation(input_type: str, score: int, label: str, signals: list[str]) -> str:
    base = (
        f"This {input_type} was evaluated using explainable credibility heuristics. "
        f"Final score: {score}/100. Final label: {label}. "
    )

    if signals:
        return base + "Main signals: " + ", ".join(signals[:6]) + "."

    return base + "No major credibility signal detected."


def analyze_text_content(content: str):
    text = normalize_content(content)

    if not text:
        return {
            "credibility_score": 0,
            "credibility_label": "No Input",
            "explanation": "No content was provided for analysis.",
            "risk_signals": ["Empty input"],
        }

    input_type = detect_input_type(text)
    score = 45
    signals = []

    sensational_penalty, sensational_signals = score_sensational_language(text)
    score -= sensational_penalty
    signals.extend(sensational_signals)

    trusted_bonus, trusted_found, trusted_signals = score_trusted_signals(text)
    score += trusted_bonus
    signals.extend(trusted_signals)

    if input_type == "url":
        reputation_delta, reputation_signals = score_url_reputation(text)
        score += reputation_delta
        signals.extend(reputation_signals)

    context_delta, context_signals = score_length_and_context(text)
    score += context_delta
    signals.extend(context_signals)

    source_delta, source_signals = score_source_presence(text)
    score += source_delta
    signals.extend(source_signals)

    balance_delta, balance_signals = score_balance_markers(text)
    score += balance_delta
    signals.extend(balance_signals)

    if trusted_found >= 2:
        score += 4

    score = max(0, min(100, score))
    label = label_from_score(score)
    explanation = build_explanation(input_type, score, label, signals)

    return {
        "credibility_score": score,
        "credibility_label": label,
        "explanation": explanation,
        "risk_signals": signals,
    }
