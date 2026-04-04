from dataclasses import dataclass
import re
from typing import List

import requests

from app.analyzer import analyze_payload
from app.config import get_settings
from app.database import get_recent_user_checks
from app.prompts import FEW_SHOT_EXAMPLES, TRUTHLENS_SYSTEM_PROMPT, build_context_instructions
from app.schemas import AssistantAnalysisSnapshot, ChatRequest, ChatResponse


GEMINI_API_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

GREETING_PATTERNS = {
    "en": ("hi", "hello", "hey", "good morning", "good evening"),
    "fr": ("salut", "bonjour", "bonsoir", "coucou"),
}

INTENT_KEYWORDS = {
    "summarize_article": ("summary", "summarize", "resume", "resumer"),
    "explain_score": ("score", "credibility", "suspicious", "why", "pourquoi", "explain"),
    "explain_trend": ("trend", "trending", "tendance", "narrative", "viral"),
    "compare_narratives": ("compare", "difference", "morocco", "world", "maroc", "monde"),
    "next_steps": ("verify", "verification", "next", "what should i verify", "quoi verifier"),
    "fact_check_text": (
        "check",
        "fact-check",
        "verify this",
        "is this true",
        "claim",
        "verifie",
        "verifier",
        "affirmation",
        "rumeur",
        "est-ce vrai",
    ),
}

URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


@dataclass(frozen=True)
class RoutedIntent:
    name: str
    language: str
    target_url: str = ""


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


def detect_language(message: str) -> str:
    normalized = (message or "").strip().lower()
    if any(token in normalized for token in GREETING_PATTERNS["fr"]) or any(
        token in normalized for token in ("maroc", "tendance", "verifier", "verifie", "affirmation", "pourquoi")
    ):
        return "fr"
    return "en"


def looks_like_greeting(message: str) -> bool:
    normalized = (message or "").strip().lower()
    if not normalized:
        return False

    return any(
        normalized == token or normalized.startswith(f"{token} ")
        for tokens in GREETING_PATTERNS.values()
        for token in tokens
    )


def extract_first_url(message: str) -> str:
    match = URL_PATTERN.search(message or "")
    return match.group(0) if match else ""


def classify_intent(payload: ChatRequest) -> RoutedIntent:
    message = (payload.message or "").strip()
    normalized = message.lower()
    language = detect_language(message)

    if looks_like_greeting(message):
        return RoutedIntent("greeting", language)

    target_url = extract_first_url(message)
    if target_url:
        return RoutedIntent("fact_check_url", language, target_url=target_url)

    if payload.selected_trend_title and any(keyword in normalized for keyword in INTENT_KEYWORDS["explain_trend"]):
        return RoutedIntent("explain_trend", language)

    if any(keyword in normalized for keyword in INTENT_KEYWORDS["compare_narratives"]):
        return RoutedIntent("compare_narratives", language)

    if payload.article_title and any(keyword in normalized for keyword in INTENT_KEYWORDS["summarize_article"]):
        return RoutedIntent("summarize_article", language)

    if (payload.article_label or payload.article_score is not None) and any(
        keyword in normalized for keyword in INTENT_KEYWORDS["explain_score"]
    ):
        return RoutedIntent("explain_score", language)

    if any(keyword in normalized for keyword in INTENT_KEYWORDS["next_steps"]):
        return RoutedIntent("next_steps", language)

    if any(keyword in normalized for keyword in INTENT_KEYWORDS["fact_check_text"]):
        return RoutedIntent("fact_check_text", language)

    return RoutedIntent("general_guidance", language)


def greeting_message(language: str) -> str:
    if language == "fr":
        return (
            "Bonjour! Je suis votre assistant TruthLens. Je peux vous aider a analyser une URL, "
            "verifier une affirmation, resumer un article ou expliquer pourquoi un sujet devient tendance. "
            "Collez simplement un lien, un texte, ou dites-moi ce que vous voulez verifier."
        )

    return (
        "Hello! I am your TruthLens assistant. I can help you analyze a URL, verify a claim, "
        "summarize an article, or explain why a topic is trending. Paste a link, a text claim, "
        "or tell me what you want to verify."
    )


def localize_verification_status(status: str, language: str) -> str:
    if language != "fr":
        return status

    mapping = {
        "Awaiting stronger corroboration": "En attente d'une corroboration plus solide",
        "Partially corroborated": "Partiellement corrobore",
        "Broadly corroborated": "Largement corrobore",
        "No verification yet": "Pas encore verifie",
    }
    return mapping.get(status, status)


def build_analysis_snapshot(result: dict, input_type: str) -> AssistantAnalysisSnapshot:
    return AssistantAnalysisSnapshot(
        input_type=input_type,
        credibility_score=result["credibility_score"],
        credibility_label=result["credibility_label"],
        source_score=result["source_score"],
        article_score=result["article_score"],
        corroboration_score=result["corroboration_score"],
        final_score=result["final_score"],
        final_label=result["final_label"],
        verification_status=result["verification_status"],
        explanation=result["explanation"],
        risk_signals=result.get("risk_signals", []),
        verification_tips=result.get("verification_tips", []),
        source_profile=result.get("source_profile"),
    )


def build_suggested_checks(payload: ChatRequest, analysis_snapshot: AssistantAnalysisSnapshot | None) -> List[str]:
    checks = []

    if analysis_snapshot:
        checks.extend(analysis_snapshot.verification_tips[:3])
    elif payload.article_label:
        checks.append(f"Verify why the content received the label '{payload.article_label}'.")
    elif payload.selected_trend_title:
        checks.append(f"Check whether '{payload.selected_trend_title}' is spreading faster than strong verification.")

    if payload.article_source:
        checks.append(f"Review the reliability and ownership of '{payload.article_source}'.")
    if payload.selected_trend_source_signals:
        checks.append("Compare the trend against stronger editorial or institutional sources.")

    checks.append("Look for at least two independent corroborating sources.")
    return checks[:4]


def build_quick_actions(intent: str, payload: ChatRequest) -> List[str]:
    if intent in {"fact_check_url", "fact_check_text"}:
        return [
            "Summarize the claim",
            "Why is this suspicious?",
            "What should I verify next?",
        ]
    if intent == "explain_trend":
        return [
            "Compare Morocco vs World narratives",
            "What is the verification gap here?",
            "Which sources should confirm this trend?",
        ]
    return [
        "Analyze this URL",
        "Check this claim",
        "Explain this trend",
        "Compare Morocco vs World narratives",
    ]


def build_context_note(payload: ChatRequest) -> str:
    notes = []
    if payload.article_title:
        notes.append(f"Focused on article: {payload.article_title}")
    if payload.selected_trend_title:
        notes.append(f"Focused on trend: {payload.selected_trend_title}")
    if payload.region_focus:
        notes.append(f"Region focus: {payload.region_focus}")
    if payload.active_view:
        notes.append(f"View: {payload.active_view}")
    return " | ".join(notes) or "TruthLens context active."


def build_local_answer(
    payload: ChatRequest,
    routed: RoutedIntent,
    analysis_snapshot: AssistantAnalysisSnapshot | None,
) -> str:
    if routed.name == "greeting":
        return greeting_message(routed.language)

    if routed.name == "fact_check_url" and analysis_snapshot:
        if routed.language == "fr":
            return (
                f"Cette URL est actuellement classee {analysis_snapshot.final_label.lower()} avec un score final de "
                f"{analysis_snapshot.final_score}/100. "
                f"Source: {analysis_snapshot.source_score}/100, qualite de l'article: {analysis_snapshot.article_score}/100, "
                f"corroboration: {analysis_snapshot.corroboration_score}/100. "
                f"Le statut actuel est: {localize_verification_status(analysis_snapshot.verification_status, routed.language)}. "
                "Considere ceci comme une aide a la verification, pas comme une verite absolue."
            )
        return (
            f"This URL is currently labelled {analysis_snapshot.final_label.lower()} with a final score of "
            f"{analysis_snapshot.final_score}/100. "
            f"Source: {analysis_snapshot.source_score}/100, article quality: {analysis_snapshot.article_score}/100, "
            f"corroboration: {analysis_snapshot.corroboration_score}/100. "
            f"{analysis_snapshot.explanation} "
            "Treat this as a verification aid, not absolute truth."
        )

    if routed.name == "fact_check_text" and analysis_snapshot:
        if routed.language == "fr":
            return (
                f"Cette affirmation est actuellement evaluee a {analysis_snapshot.final_score}/100 et etiquetee "
                f"'{analysis_snapshot.final_label}'. "
                f"Source initiale: {analysis_snapshot.source_score}/100, qualite de l'article: {analysis_snapshot.article_score}/100, "
                f"corroboration: {analysis_snapshot.corroboration_score}/100. "
                f"Le statut actuel est: {localize_verification_status(analysis_snapshot.verification_status, routed.language)}. "
                "Il faut encore verifier la source d'origine, la date et la corroboration."
            )
        return (
            f"This claim is currently rated {analysis_snapshot.final_score}/100 and labelled "
            f"'{analysis_snapshot.final_label}'. "
            f"Source prior: {analysis_snapshot.source_score}/100, article quality: {analysis_snapshot.article_score}/100, "
            f"corroboration: {analysis_snapshot.corroboration_score}/100. "
            f"{analysis_snapshot.explanation} "
            "You should still verify the original source, date, and corroboration."
        )

    if routed.name == "summarize_article" and payload.article_summary:
        if routed.language == "fr":
            return (
                f"Voici le resume court: {payload.article_summary} "
                "Pour le verifier, confirmez les acteurs cites, la date, et si des sources plus solides racontent la meme histoire."
            )
        return (
            f"Here is the short summary: {payload.article_summary} "
            "To verify it, confirm the named actors, date, and whether stronger sources tell the same story."
        )

    if routed.name == "explain_score" and (payload.article_score is not None or analysis_snapshot):
        score = payload.article_score if payload.article_score is not None else analysis_snapshot.final_score
        label = payload.article_label or analysis_snapshot.final_label
        explanation = analysis_snapshot.explanation if analysis_snapshot else payload.article_summary or ""
        if routed.language == "fr":
            return (
                f"L'estimation actuelle de TruthLens est de {score}/100 avec l'etiquette '{label}'. "
                f"{'Cette estimation combine la fiabilite de la source, la qualite de l article et la corroboration.'}"
            )
        return (
            f"The current TruthLens estimate is {score}/100 with the label '{label}'. "
            f"{explanation or 'This reflects source baseline reliability, article quality, and corroboration strength.'}"
        )

    if routed.name == "explain_trend" and payload.selected_trend_title:
        warning = ""
        if (payload.selected_trend_verification_gap_score or 0) >= 18:
            warning = (
                " Elle circule plus vite que sa verification solide, donc traite-la comme un signal d'alerte precoce."
                if routed.language == "fr"
                else " It is spreading faster than strong verification, so treat it as an early-warning narrative."
            )

        signals = []
        if payload.selected_trend_platform_signals:
            signals.append(
                (
                    "des signaux sociaux provenant de " + ", ".join(payload.selected_trend_platform_signals[:3])
                    if routed.language == "fr"
                    else "social signals from " + ", ".join(payload.selected_trend_platform_signals[:3])
                )
            )
        if payload.selected_trend_source_signals:
            signals.append(
                (
                    "un renfort editorial venant de " + ", ".join(payload.selected_trend_source_signals[:3])
                    if routed.language == "fr"
                    else "news reinforcement from " + ", ".join(payload.selected_trend_source_signals[:3])
                )
            )

        signal_text = (
            ", ".join(signals)
            if signals
            else ("les signaux de tendance disponibles" if routed.language == "fr" else "available trend signals")
        )
        if routed.language == "fr":
            return (
                f"'{payload.selected_trend_title}' devient tendance dans "
                f"{payload.selected_trend_region or payload.region_focus or 'le flux actif'} parce que TruthLens observe "
                f"{signal_text}.{warning}"
            )
        return (
            f"'{payload.selected_trend_title}' is trending in {payload.selected_trend_region or payload.region_focus or 'the feed'} "
            f"because TruthLens is seeing {signal_text}.{warning}"
        )

    if routed.name == "compare_narratives":
        morocco = ", ".join(payload.morocco_trends[:3]) or "no strong Morocco trend detected yet"
        world = ", ".join(payload.world_trends[:3]) or "no strong World trend detected yet"
        if routed.language == "fr":
            morocco = ", ".join(payload.morocco_trends[:3]) or "aucune forte tendance Maroc detectee pour le moment"
            world = ", ".join(payload.world_trends[:3]) or "aucune forte tendance Monde detectee pour le moment"
            return (
                f"Le Maroc est actuellement domine par: {morocco}. "
                f"Le Monde est actuellement domine par: {world}. "
                "Compare-les en verifiant quel cote a la meilleure corroboration et le plus grand ecart de verification."
            )
        return (
            f"Morocco is currently dominated by: {morocco}. "
            f"World coverage is currently dominated by: {world}. "
            "Compare them by checking whether one side has stronger source corroboration or a larger verification gap."
        )

    if routed.name == "next_steps":
        if routed.language == "fr":
            return (
                "Commencez par la source d'origine, confirmez la date de publication, recherchez les institutions ou personnes citees, "
                "puis comparez avec au moins deux sources independantes."
            )
        return (
            "Start with the original source, confirm the publication date, look for named institutions or officials, "
            "then compare with at least two independent sources."
        )

    if routed.language == "fr":
        return (
            "Je peux vous aider a verifier une URL, controler une affirmation, resumer un article, "
            "expliquer un score ou interpreter une tendance. Collez un lien ou un texte pour continuer."
        )
    return (
        "I can help you verify a URL, check a text claim, summarize an article, explain a score, "
        "or interpret a trend. Paste a claim or select an article or trend to continue."
    )


def build_gemini_user_prompt(
    payload: ChatRequest,
    routed: RoutedIntent,
    analysis_snapshot: AssistantAnalysisSnapshot | None,
) -> str:
    lines = [
        f"User message: {payload.message.strip()}",
        f"Detected response language: {'French' if routed.language == 'fr' else 'English'}",
        build_memory_snippet(),
        build_context_instructions(payload, routed.name, analysis_snapshot),
        (
            "Answer in French. For greetings, start with: "
            "'Bonjour! Je suis votre assistant TruthLens.' Then briefly explain what you can do."
            if routed.language == "fr"
            else "Answer in English. For greetings, briefly introduce TruthLens Assistant and what it can do."
        ),
        "Stay concise, explain uncertainty honestly, and propose practical next checks.",
    ]
    return "\n\n".join(lines)


def build_few_shot_examples() -> str:
    lines = ["Examples of ideal TruthLens behavior:"]
    for example in FEW_SHOT_EXAMPLES:
        lines.append(f"User: {example['user']}")
        lines.append(f"Assistant: {example['assistant']}")
    return "\n".join(lines)


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
                answer="Posez une question, collez une URL ou une affirmation, et TruthLens Assistant vous aidera a la verifier.",
                suggested_checks=["Analyser une URL", "Verifier une affirmation", "Expliquer une tendance"],
                model="local-fallback",
                grounded_in_scope=True,
                intent="empty",
                context_note=build_context_note(payload),
                quick_actions=build_quick_actions("general_guidance", payload),
            )

        routed = classify_intent(payload)
        analysis_snapshot = self.maybe_analyze(payload, routed)

        if routed.name == "greeting":
            return ChatResponse(
                answer=greeting_message(routed.language),
                suggested_checks=[
                    "Collez une URL a analyser.",
                    "Collez une affirmation a verifier.",
                    "Demandez pourquoi un sujet devient tendance.",
                ],
                model="local-fallback",
                grounded_in_scope=True,
                intent=routed.name,
                context_note=build_context_note(payload),
                quick_actions=build_quick_actions(routed.name, payload),
            )

        if not self.is_configured():
            return self.build_local_response(payload, routed, analysis_snapshot)

        try:
            answer, used_model = self.ask_gemini(payload, routed, analysis_snapshot)
        except RuntimeError:
            return self.build_local_response(payload, routed, analysis_snapshot)

        if not answer:
            return self.build_local_response(payload, routed, analysis_snapshot)

        return ChatResponse(
            answer=answer,
            suggested_checks=build_suggested_checks(payload, analysis_snapshot),
            model=used_model,
            grounded_in_scope=True,
            intent=routed.name,
            context_note=build_context_note(payload),
            quick_actions=build_quick_actions(routed.name, payload),
            analysis_snapshot=analysis_snapshot,
        )

    def maybe_analyze(self, payload: ChatRequest, routed: RoutedIntent) -> AssistantAnalysisSnapshot | None:
        try:
            if routed.name == "fact_check_url" and routed.target_url:
                return build_analysis_snapshot(analyze_payload(url=routed.target_url), "url")

            if routed.name == "fact_check_text":
                return build_analysis_snapshot(analyze_payload(text=payload.message.strip()), "text")
        except Exception:
            return None

        return None

    def build_local_response(
        self,
        payload: ChatRequest,
        routed: RoutedIntent,
        analysis_snapshot: AssistantAnalysisSnapshot | None,
    ) -> ChatResponse:
        return ChatResponse(
            answer=build_local_answer(payload, routed, analysis_snapshot),
            suggested_checks=build_suggested_checks(payload, analysis_snapshot),
            model="local-fallback",
            grounded_in_scope=True,
            intent=routed.name,
            context_note=build_context_note(payload),
            quick_actions=build_quick_actions(routed.name, payload),
            analysis_snapshot=analysis_snapshot,
        )

    def ask_gemini(
        self,
        payload: ChatRequest,
        routed: RoutedIntent,
        analysis_snapshot: AssistantAnalysisSnapshot | None,
    ) -> tuple[str, str]:
        body = {
            "system_instruction": {
                "parts": [
                    {
                        "text": "\n\n".join(
                            [
                                TRUTHLENS_SYSTEM_PROMPT,
                                build_few_shot_examples(),
                            ]
                        )
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": build_gemini_user_prompt(payload, routed, analysis_snapshot),
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.25,
                "maxOutputTokens": 550,
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
