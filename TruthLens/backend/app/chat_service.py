from typing import List

import requests

from app.config import get_settings
from app.schemas import ChatRequest, ChatResponse

ASSISTANT_SCOPE: List[str] = [
    "summarize a news item or claim",
    "explain a credibility score in simple terms",
    "reformulate a claim into a clearer fact-checking question",
    "suggest practical verification steps",
]

ASSISTANT_BOUNDARY_MESSAGE = (
    "I can help with TruthLens tasks only: summarize a claim, explain a score, "
    "rephrase a claim for verification, or suggest fact-checking steps."
)
GEMINI_API_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def build_chat_system_prompt() -> str:
    joined_scope = "; ".join(ASSISTANT_SCOPE)
    return (
        "You are the TruthLens Assistant. "
        "Stay focused on fact-checking support and explainability. "
        f"You may only: {joined_scope}. "
        "Do not claim certainty, do not invent evidence, and do not present opinions as facts. "
        "When the request goes outside this scope, refuse briefly and redirect to verification help."
    )


def build_chat_user_prompt(payload: ChatRequest) -> str:
    context_lines = [
        f"User request: {payload.message.strip()}",
    ]

    if payload.article_title:
        context_lines.append(f"Article title: {payload.article_title.strip()}")

    if payload.article_summary:
        context_lines.append(f"Article summary: {payload.article_summary.strip()}")

    if payload.article_score is not None:
        context_lines.append(f"Credibility score: {payload.article_score}/100")

    if payload.article_label:
        context_lines.append(f"Credibility label: {payload.article_label.strip()}")

    context_lines.append(
        "Reply with a concise assistant answer and concrete verification guidance."
    )
    return "\n".join(context_lines)


def build_suggested_checks(payload: ChatRequest) -> List[str]:
    checks = []

    if payload.article_label:
        checks.append(f"Verify why the content was labelled '{payload.article_label}'.")

    if payload.article_score is not None:
        checks.append(f"Review which signals influenced the {payload.article_score}/100 score.")

    if payload.article_title:
        checks.append("Search for corroboration from official or institutional sources.")

    checks.append("Compare the claim with at least two independent sources.")
    return checks[:3]


def extract_answer(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""

    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [part.get("text", "").strip() for part in parts if part.get("text")]
    return "\n".join(part for part in text_parts if part).strip()


class ChatService:
    def __init__(self):
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return self.settings.gemini_enabled

    def chat(self, payload: ChatRequest) -> ChatResponse:
        trimmed_message = payload.message.strip()

        if not trimmed_message:
            return self.build_placeholder_response(payload)

        if not self.is_configured():
            return ChatResponse(
                answer=(
                    "Gemini is not configured yet. Add a valid GEMINI_API_KEY in "
                    "backend/.env or backend/.env.example to enable live assistant answers."
                ),
                suggested_checks=build_suggested_checks(payload),
                model=self.settings.gemini_model,
                grounded_in_scope=True,
            )

        try:
            answer, model_used = self.ask_gemini(payload)
        except RuntimeError as exc:
            detail = str(exc)
            if "RESOURCE_EXHAUSTED" in detail or "quota" in detail.lower():
                return ChatResponse(
                    answer=(
                        "Gemini is configured, but the current API quota is exhausted right now. "
                        "Use the verification steps below, or retry after the quota resets."
                    ),
                    suggested_checks=build_suggested_checks(payload),
                    model=self.settings.gemini_model,
                    grounded_in_scope=True,
                )
            raise

        if not answer:
            return self.build_placeholder_response(payload)

        return ChatResponse(
            answer=answer,
            suggested_checks=build_suggested_checks(payload),
            model=model_used,
            grounded_in_scope=True,
        )

    def ask_gemini(self, payload: ChatRequest) -> tuple[str, str]:
        request_payload = {
            "system_instruction": {
                "parts": [
                    {
                        "text": build_chat_system_prompt(),
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": build_chat_user_prompt(payload),
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 350,
            },
        }

        candidate_models = []
        for name in [self.settings.gemini_model, "gemini-2.0-flash", "gemini-2.5-flash"]:
            if name not in candidate_models:
                candidate_models.append(name)

        last_error = "Gemini request failed."

        for model_name in candidate_models:
            response = requests.post(
                GEMINI_API_TEMPLATE.format(model=model_name),
                params={"key": self.settings.gemini_api_key},
                headers={"Content-Type": "application/json"},
                json=request_payload,
                timeout=self.settings.gemini_timeout_seconds,
            )

            if response.ok:
                answer = extract_answer(response.json())
                if not answer:
                    raise RuntimeError("Gemini returned an empty response.")
                return answer, model_name

            if response.status_code in {404, 429}:
                last_error = response.text.strip() or last_error
                continue

            raise RuntimeError(response.text.strip() or "Gemini request failed.")

        raise RuntimeError(last_error)

    def build_placeholder_response(self, payload: ChatRequest) -> ChatResponse:
        trimmed_message = payload.message.strip()

        if not trimmed_message:
            return ChatResponse(
                answer="Please enter a question or claim for the TruthLens assistant.",
                suggested_checks=[
                    "Add the exact claim, URL, or headline you want to verify.",
                ],
                model=self.settings.gemini_model,
                grounded_in_scope=True,
            )

        return ChatResponse(
            answer=ASSISTANT_BOUNDARY_MESSAGE,
            suggested_checks=build_suggested_checks(payload),
            model=self.settings.gemini_model,
            grounded_in_scope=True,
        )
