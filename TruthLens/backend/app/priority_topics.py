from dataclasses import dataclass


MOROCCO_SCOPE_TERMS = (
    "Morocco",
    "Moroccan",
    "Rabat",
    "Casablanca",
    "Tangier",
    "Marrakech",
    "Agadir",
)


@dataclass(frozen=True)
class PriorityTopicBundle:
    slug: str
    label: str
    regions: tuple[str, ...]
    keywords: tuple[str, ...]
    priority_weight: int
    category: str = "International"
    conflict_related: bool = False
    region_scope_terms: tuple[str, ...] = ()


PRIORITY_TOPIC_BUNDLES = (
    PriorityTopicBundle(
        slug="conflict-escalation",
        label="Conflict Escalation",
        regions=("world",),
        keywords=(
            "war",
            "conflict",
            "invasion",
            "military escalation",
            "airstrike",
            "shelling",
            "missile attack",
            "drone strike",
            "offensive",
            "troop deployment",
        ),
        priority_weight=24,
        conflict_related=True,
    ),
    PriorityTopicBundle(
        slug="ceasefire-and-hostages",
        label="Ceasefire Watch",
        regions=("world",),
        keywords=(
            "ceasefire",
            "truce",
            "peace talks",
            "hostage deal",
            "hostage release",
            "negotiation",
            "mediated talks",
        ),
        priority_weight=22,
        conflict_related=True,
    ),
    PriorityTopicBundle(
        slug="humanitarian-crisis",
        label="Humanitarian Crisis",
        regions=("world",),
        keywords=(
            "humanitarian crisis",
            "aid convoy",
            "civilian casualties",
            "displaced families",
            "refugees",
            "famine",
            "emergency aid",
        ),
        priority_weight=20,
        conflict_related=True,
    ),
    PriorityTopicBundle(
        slug="disruption-and-strikes",
        label="Disruption & Strikes",
        regions=("world", "ma"),
        keywords=(
            "strike",
            "general strike",
            "walkout",
            "protest",
            "shutdown",
            "state of emergency",
            "crisis",
        ),
        priority_weight=17,
        conflict_related=False,
    ),
    PriorityTopicBundle(
        slug="morocco-alerts",
        label="Morocco Alert",
        regions=("ma",),
        keywords=(
            "strike",
            "protest",
            "disruption",
            "water shortage",
            "power outage",
            "border tension",
            "emergency",
        ),
        priority_weight=18,
        category="Society",
        conflict_related=False,
        region_scope_terms=MOROCCO_SCOPE_TERMS,
    ),
)


def get_priority_topics(region: str) -> list[PriorityTopicBundle]:
    normalized = (region or "world").strip().lower()
    return [
        bundle
        for bundle in PRIORITY_TOPIC_BUNDLES
        if normalized in bundle.regions
    ]


def match_priority_topics(text: str, region: str) -> list[PriorityTopicBundle]:
    normalized_text = (text or "").lower()
    matches = []

    for bundle in get_priority_topics(region):
        if bundle_match_score(normalized_text, bundle) > 0:
            matches.append(bundle)

    return matches


def _quote_term(term: str) -> str:
    return f'"{term}"' if " " in term else term


def build_topic_query(bundle: PriorityTopicBundle, region: str) -> str:
    keyword_query = " OR ".join(_quote_term(term) for term in bundle.keywords)
    if region == "ma" and bundle.region_scope_terms:
        region_query = " OR ".join(_quote_term(term) for term in bundle.region_scope_terms)
        return f"({region_query}) AND ({keyword_query})"
    return keyword_query


def bundle_match_score(text: str, bundle: PriorityTopicBundle) -> int:
    normalized_text = (text or "").lower()
    score = 0

    for keyword in bundle.keywords:
        lowered = keyword.lower()
        if lowered in normalized_text:
            score += 2 if " " in lowered else 1

    if bundle.region_scope_terms and any(term.lower() in normalized_text for term in bundle.region_scope_terms):
        score += 1

    return score
