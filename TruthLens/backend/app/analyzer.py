def analyze_text_content(content: str):
    text = content.lower()

    score = 50
    risk_signals = []

    sensational_words = [
        "shocking", "secret", "cover-up", "scandal", "urgent",
        "incroyable", "choc", "scandale", "secret", "complot"
    ]

    trusted_words = [
        "official", "confirmed", "parliament", "government",
        "source", "report", "official statement", "confirmed by"
    ]

    for word in sensational_words:
        if word in text:
            score -= 10
            risk_signals.append(f"Sensational term detected: {word}")

    for word in trusted_words:
        if word in text:
            score += 8

    if len(content.split()) < 20:
        score -= 10
        risk_signals.append("Very short content, limited context")

    if "http" not in text and "source" not in text and "confirmed" not in text:
        score -= 10
        risk_signals.append("No explicit sourcing detected")

    score = max(0, min(100, score))

    if score >= 80:
        label = "Reliable"
    elif score >= 60:
        label = "Needs Context"
    elif score >= 40:
        label = "Unverified"
    elif score >= 20:
        label = "Suspicious"
    else:
        label = "High Risk"

    explanation = (
        f"The content was evaluated using simple credibility heuristics. "
        f"Final score: {score}/100. Main concerns: {', '.join(risk_signals) if risk_signals else 'no major risk signal detected'}."
    )

    return {
        "credibility_score": score,
        "credibility_label": label,
        "explanation": explanation,
        "risk_signals": risk_signals
    }