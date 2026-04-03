from typing import List

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


class ChatService:
    def __init__(self):
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return self.settings.gemini_enabled

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
            suggested_checks=[
                "Paste the exact claim or article URL.",
                "Ask for a short summary before checking details.",
                "Ask which sources or institutions should confirm the claim.",
            ],
            model=self.settings.gemini_model,
            grounded_in_scope=True,
        )
