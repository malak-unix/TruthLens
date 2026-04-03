from typing import List

import requests

from app.config import get_settings
from app.database import get_recent_user_checks
from app.schemas import ChatRequest, ChatResponse


GEMINI_API_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

ASSISTANT_BOUNDARY_MESSAGE = (
    "I can help only with TruthLens tasks: explain a credibility score, summarize a news item, "
    "rephrase a claim for fact-checking, compare risky vs better-supported narratives, or suggest verification steps."
)


def build_chat_system_prompt() -> str:
    return (
        "You are the TruthLens Assistant, a domain-specific fact-check support assistant. "
        "You do not decide absolute truth. "
        "You estimate credibility using explainable signals and help the user verify responsibly. "
        "Be concise, practical, and product-specific. "
        "Never invent evidence. Never present speculation as confirmed fact. "
        "Always keep the answer grounded in the article context, risk signals, and verification workflow."
    )


def build_memory_snippet() -> str:
    checks = get_recent_user_checks(limit=5)
    if not checks:
        return "No recent verification memory available."

    lines = ["Recent verification memory:"]
    for item in checks:
        lines.append(
            f"- {item['input_type']} | label={item['credibility_label']} | score={item['credibility_score']}"
        )
    return "\n".join(lines)


def build_chat_user_prompt(payload: ChatRequest) -> str:
    lines = [
        f"User message: {payload.message.strip()}",
        build_memory_snippet(),
    ]

    if payload.article_title:
        lines.append(f"Article title: {payload.article_title}")
    if payload.article_summary:
        lines.append(f"Article summary: {payload.article_summary}")
    if payload.article_score is not None:
        lines.append(f"Article score: {payload.article_score}/100")
    if payload.article_label:
        lines.append(f"Article label: {payload.article_label}")
    if payload.article_url:
        lines.append(f"Article URL: {payload.article_url}")
    if payload.article_source:
        lines.append(f"Article source: {payload.article_source}")
    if payload.article_region:
        lines.append(f"Article region: {payload.article_region}")
    if payload.risk_signals:
        lines.append("Risk signals: " + ", ".join(payload.risk_signals[:6]))

    lines.append(
        "Respond with a concise answer and practical next checks. "
        "If the content looks weakly confirmed, say so clearly."
    )
    return "\n".join(lines)


def build_suggested_checks(payload: ChatRequest) -> List[str]:
    checks = []

    if payload.article_label:
        checks.append(f"Verify why the content received the label '{payload.article_label}'.")
    if payload.article_score is not None:
        checks.append(f"Inspect the signals behind the {payload.article_score}/100 credibility score.")
    if payload.article_source:
        checks.append(f"Check the reliability and ownership of the source '{payload.article_source}'.")

    checks.append("Look for at least two independent corroborating sources.")
    return checks[:4]


def build_local_fallback_answer(payload: ChatRequest) -> str:
    message = payload.message.strip().lower()

    if not message:
        return "Please enter a question or claim for the TruthLens assistant."

    if any(token in message for token in ["summary", "summarize", "resume"]):
        if payload.article_summary:
            return (
                f"Summary: {payload.article_summary} "
                "Next, verify the primary source, publication date, and whether stronger sources report the same claim."
            )

    if any(token in message for token in ["score", "why", "explain", "credibility", "pourquoi"]):
        if payload.article_score is not None and payload.article_label:
            return (
                f"This item is currently rated {payload.article_score}/100 and labelled '{payload.article_label}'. "
                "That estimate usually depends on source trust, attribution quality, context richness, and suspicious language cues."
            )

    if any(token in message for token in ["rephrase", "rewrite", "reformulate"]):
        if payload.article_title:
            return (
                f"A clearer verification question is: 'What verified evidence confirms or disproves the claim that {payload.article_title}?'"
            )

    return (
        "Start from the original source, then verify the named actors, date, official statements, and at least one independent corroboration."
    )


def extract_answer(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""

    parts = candidates[0].get("content", {}).get("parts", [])
    texts = [part.get("text", "").strip() for part in parts if part.get("text")]
    return "\n".join(item for item in texts if item).strip()


class ChatService:
    def __init__(self):
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return self.settings.gemini_enabled

    def chat(self, payload: ChatRequest) -> ChatResponse:
        if not payload.message.strip():
            return ChatResponse(
                answer="Please enter a question or claim for the TruthLens assistant.",
                suggested_checks=["Ask about a score, summary, or next verification steps."],
                model="local-fallback",
                grounded_in_scope=True,
            )

        if not self.is_configured():
            return ChatResponse(
                answer=build_local_fallback_answer(payload),
                suggested_checks=build_suggested_checks(payload),
                model="local-fallback",
                grounded_in_scope=True,
            )

        try:
            answer, used_model = self.ask_gemini(payload)
        except RuntimeError:
            return ChatResponse(
                answer=build_local_fallback_answer(payload),
                suggested_checks=build_suggested_checks(payload),
                model="local-fallback",
                grounded_in_scope=True,
            )

        if not answer:
            answer = ASSISTANT_BOUNDARY_MESSAGE

        return ChatResponse(
            answer=answer,
            suggested_checks=build_suggested_checks(payload),
            model=used_model,
            grounded_in_scope=True,
        )

    def ask_gemini(self, payload: ChatRequest) -> tuple[str, str]:
        body = {
            "system_instruction": {
                "parts": [{"text": build_chat_system_prompt()}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": build_chat_user_prompt(payload)}],
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 400,
            },
        }

        candidates = []
        for model_name in [self.settings.gemini_model, "gemini-2.5-flash", "gemini-2.0-flash"]:
            if model_name not in candidates:
                candidates.append(model_name)

        last_error = "Gemini request failed."

        for model_name in candidates:
            try:
                response = requests.post(
                    GEMINI_API_TEMPLATE.format(model=model_name),
                    params={"key": self.settings.gemini_api_key},
                    headers={"Content-Type": "application/json"},
                    json=body,
                    timeout=self.settings.gemini_timeout_seconds,
                )
            except requests.RequestException as exc:
                last_error = str(exc)
                continue

            if response.ok:
                answer = extract_answer(response.json())
                if answer:
                    return answer, model_name
                last_error = "Gemini returned an empty response."
                continue

            last_error = response.text.strip() or last_error

        raise RuntimeError(last_error)