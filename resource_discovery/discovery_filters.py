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
    }


def build_discovery_query(query="", filters=None):
    """Combine free text and user intent into the Brave Search query."""
    normalized_filters = normalize_filters(filters)
    parts = []

    query = (query or "").strip()

    if query:
        parts.append(query)

    # Skills are already concise search terms, so include them directly.
    parts.extend(normalized_filters["skills"])

    # Add lightweight context to degree and career selections so web search
    # favors learning/career resources rather than unrelated pages.
    for degree_program in normalized_filters["degree_programs"]:
        parts.append(f"{degree_program} learning resources")

    for career_field in normalized_filters["career_fields"]:
        parts.append(f"{career_field} skills")

    return " ".join(parts).strip()
