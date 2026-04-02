SENSATIONAL_WORDS = [
    "shocking", "secret", "cover-up", "scandal", "urgent",
    "incroyable", "choc", "scandale", "complot", "viral",
    "breaking", "exclusive", "miracle", "partagez", "share"
]

TRUSTED_WORDS = [
    "official", "confirmed", "parliament", "government",
    "report", "ministry", "statement", "press release",
    "communique", "source officielle", "confirmed by"
]

TRUSTED_DOMAINS = [
    "gov", "who.int", "un.org", "guardian", "lematin",
    "mapnews", "reuters", "bbc", "apnews"
]

SUSPICIOUS_DOMAINS = [
    "blogspot", "telegram", "rumor", "viral", "unknown"
]


def detect_input_type(content: str) -> str:
    content = content.strip().lower()
    if content.startswith("http://") or content.startswith("https://"):
        return "url"
    return "text"


def score_sensational_language(text: str):
    penalty = 0
    signals = []

    for word in SENSATIONAL_WORDS:
        if word in text:
            penalty += 8
            signals.append(f"Sensational term detected: {word}")

    return penalty, signals


def score_trusted_signals(text: str):
    bonus = 0
    found = 0

    for word in TRUSTED_WORDS:
        if word in text:
            bonus += 6
            found += 1

    return bonus, found


def score_url_reputation(text: str):
    delta = 0
    signals = []

    for domain in TRUSTED_DOMAINS:
        if domain in text:
            delta += 20
            signals.append(f"Trusted domain detected: {domain}")
            break

    for domain in SUSPICIOUS_DOMAINS:
        if domain in text:
            delta -= 15
            signals.append(f"Potentially weak source detected: {domain}")
            break

    return delta, signals


def score_length_and_context(text: str):
    words = text.split()
    signals = []
    delta = 0

    if len(words) < 8:
        delta -= 20
        signals.append("Very short content, almost no context")
    elif len(words) < 20:
        delta -= 10
        signals.append("Short content, limited context")
    elif len(words) > 40:
        delta += 5

    return delta, signals


def score_source_presence(text: str):
    source_terms = ["source", "confirmed", "report", "statement", "official"]

    if any(term in text for term in source_terms):
        return 8, []

    return -10, ["No explicit sourcing detected"]


def label_from_score(score: int) -> str:
    if score >= 80:
        return "Reliable"
    elif score >= 60:
        return "Needs Context"
    elif score >= 40:
        return "Unverified"
    elif score >= 20:
        return "Suspicious"
    return "High Risk"


def build_explanation(input_type: str, score: int, label: str, risk_signals: list[str]) -> str:
    base = (
        f"This {input_type} was evaluated using explainable credibility heuristics. "
        f"Final score: {score}/100. Final label: {label}. "
    )

    if risk_signals:
        return base + "Main signals: " + ", ".join(risk_signals) + "."

    return base + "No major risk signal detected."


def analyze_text_content(content: str):
    text = content.strip().lower()

    if not text:
        return {
            "credibility_score": 0,
            "credibility_label": "No Input",
            "explanation": "No content was provided for analysis.",
            "risk_signals": ["Empty input"]
        }

    input_type = detect_input_type(text)
    score = 50
    risk_signals = []

    sensational_penalty, sensational_signals = score_sensational_language(text)
    score -= sensational_penalty
    risk_signals.extend(sensational_signals)

    trusted_bonus, trusted_found = score_trusted_signals(text)
    score += trusted_bonus

    reputation_delta, reputation_signals = score_url_reputation(text)
    score += reputation_delta
    risk_signals.extend(reputation_signals)

    context_delta, context_signals = score_length_and_context(text)
    score += context_delta
    risk_signals.extend(context_signals)

    source_delta, source_signals = score_source_presence(text)
    score += source_delta
    risk_signals.extend(source_signals)

    if trusted_found >= 2:
        score += 5

    score = max(0, min(100, score))
    label = label_from_score(score)
    explanation = build_explanation(input_type, score, label, risk_signals)

    return {
        "credibility_score": score,
        "credibility_label": label,
        "explanation": explanation,
        "risk_signals": risk_signals
    }