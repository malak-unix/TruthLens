from app.schemas import AssistantAnalysisSnapshot, ChatRequest


def build_behavior_policy() -> str:
    return (
        "Response policy:\n"
        "- For greetings: introduce TruthLens Assistant and mention core capabilities.\n"
        "- For URL or text fact-check requests: explain the credibility estimate, main signals, and next checks.\n"
        "- For score explanation: translate the score into plain language.\n"
        "- For trend explanation: explain what is trending, why it matters, and whether verification lags behind virality.\n"
        "- For Morocco vs World comparisons: compare narratives clearly and avoid false certainty.\n"
        "- End with practical next steps when useful."
    )


def build_context_instructions(payload: ChatRequest, intent: str, analysis_snapshot: AssistantAnalysisSnapshot | None) -> str:
    lines = [
        f"Detected intent: {intent}",
        build_behavior_policy(),
    ]

    if payload.region_focus:
        lines.append(f"Region focus: {payload.region_focus}")
    if payload.active_view:
        lines.append(f"Active product view: {payload.active_view}")

    if payload.article_title:
        lines.append(f"Selected article title: {payload.article_title}")
    if payload.article_summary:
        lines.append(f"Selected article summary: {payload.article_summary}")
    if payload.article_score is not None:
        lines.append(f"Selected article score: {payload.article_score}/100")
    if payload.article_label:
        lines.append(f"Selected article label: {payload.article_label}")
    if payload.article_source:
        lines.append(f"Selected article source: {payload.article_source}")
    if payload.article_region:
        lines.append(f"Selected article region: {payload.article_region}")

    if payload.selected_trend_title:
        lines.append(f"Selected trend: {payload.selected_trend_title}")
    if payload.selected_trend_region:
        lines.append(f"Selected trend region: {payload.selected_trend_region}")
    if payload.selected_trend_freshness:
        lines.append(f"Selected trend freshness: {payload.selected_trend_freshness}")
    if payload.selected_trend_verification_gap_score is not None:
        lines.append(f"Selected trend verification gap score: {payload.selected_trend_verification_gap_score}")
    if payload.selected_trend_source_signals:
        lines.append("Selected trend news signals: " + ", ".join(payload.selected_trend_source_signals[:5]))
    if payload.selected_trend_platform_signals:
        lines.append("Selected trend platform signals: " + ", ".join(payload.selected_trend_platform_signals[:5]))
    if payload.selected_trend_confidence_note:
        lines.append(f"Selected trend confidence note: {payload.selected_trend_confidence_note}")

    if payload.morocco_trends:
        lines.append("Current Morocco trends: " + ", ".join(payload.morocco_trends[:6]))
    if payload.world_trends:
        lines.append("Current World trends: " + ", ".join(payload.world_trends[:6]))

    if payload.risk_signals:
        lines.append("Risk signals: " + ", ".join(payload.risk_signals[:6]))

    if analysis_snapshot:
        lines.append(
            "Local analysis snapshot: "
            f"{analysis_snapshot.credibility_label} {analysis_snapshot.credibility_score}/100."
        )
        lines.append(
            "Score breakdown: "
            f"source={analysis_snapshot.source_score}/100, "
            f"article={analysis_snapshot.article_score}/100, "
            f"corroboration={analysis_snapshot.corroboration_score}/100."
        )
        lines.append(f"Verification status: {analysis_snapshot.verification_status}")
        lines.append("Snapshot explanation: " + analysis_snapshot.explanation)
        if analysis_snapshot.risk_signals:
            lines.append("Snapshot signals: " + ", ".join(analysis_snapshot.risk_signals[:6]))

    if payload.history:
        compact_history = []
        for item in payload.history[-6:]:
            role = (item.get("role") or "user").strip()
            content = (item.get("content") or "").strip()
            if content:
                compact_history.append(f"{role}: {content}")
        if compact_history:
            lines.append("Recent conversation:\n" + "\n".join(compact_history))

    return "\n".join(lines)
