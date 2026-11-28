"""Helpers for turning landing-page intent selections into a web-search query.

The Django Category table is the authoritative source of available Skill,
Degree Program, and Career Field options. This module intentionally does not
keep a second hard-coded option list.
"""


def normalize_filter_values(values):
    if not values:
        return []

    return [
        str(value).strip()
        for value in values
        if str(value).strip()
    ]


def normalize_filters(filters=None):
    """Return a predictable three-group filter structure for discovery."""
    filters = filters or {}

    return {
        "skills": normalize_filter_values(filters.get("skills")),
        "degree_programs": normalize_filter_values(
            filters.get("degree_programs")
        ),
        "career_fields": normalize_filter_values(
            filters.get("career_fields")
        ),
        "prices": normalize_filter_values(filters.get("prices")),
        "sources": normalize_filter_values(filters.get("sources")),
        "resource_types": normalize_filter_values(filters.get("resource_types")),
        "formats": normalize_filter_values(filters.get("formats")),
        "difficulties": normalize_filter_values(filters.get("difficulties")),
    }


def _intent_group(values, suffix=""):
    """Express alternatives within one intent group, without broad substring matching.

    Quoting multiword names preserves phrases; parentheses and OR keep multiple
    selections alternatives rather than accidentally requiring every value.
    """
    terms = []
    seen = set()
    for value in values:
        cleaned = " ".join(str(value).replace('"', ' ').split())
        if not cleaned or cleaned.casefold() in seen:
            continue
        seen.add(cleaned.casefold())
        term = f'"{cleaned}"' if " " in cleaned else cleaned
        terms.append(term)
    if not terms:
        return ""
    expression = terms[0] if len(terms) == 1 else "(" + " OR ".join(terms) + ")"
    return f"{expression} {suffix}".strip()


def build_discovery_query(query="", filters=None):
    """Guide Brave relevance with intent; leave concrete filters to post-matching.

    OR is used within each intent group. Different groups provide complementary
    search context; no local taxonomy matching or per-result DB queries occur.
    """
    normalized_filters = normalize_filters(filters)
    parts = []
    query = (query or "").strip()
    if query:
        parts.append(query)

    for group, suffix in (
        ("skills", ""),
        ("degree_programs", "learning resources"),
        ("career_fields", "skills"),
    ):
        expression = _intent_group(normalized_filters[group], suffix)
        if expression:
            parts.append(expression)

    if not parts and any(normalized_filters.values()):
        parts.append("educational learning resources tutorials")
        if len(normalized_filters["sources"]) == 1:
            source = normalized_filters["sources"][0].casefold().strip()
            if source in {"youtube", "youtube.com", "www.youtube.com"}:
                parts.append("site:youtube.com")
        for group in ("resource_types", "difficulties", "prices"):
            values = normalized_filters[group]
            if len(values) == 1:
                value = values[0].casefold().strip()
                if value in {"course", "article", "collection", "beginner", "intermediate", "advanced", "free"}:
                    parts.append(value)

    return " ".join(parts).strip()
