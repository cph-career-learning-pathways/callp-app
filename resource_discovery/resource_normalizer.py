import html
import re

# ADDED as part of issue #32 resolution:
# Define classifications permitted by the existing database schema.
RESOURCE_TYPES = {
    "course",
    "article",
    "collection",
}

RESOURCE_FORMATS = {
    "video",
    "document",
    "webpage",
    "mixed",
}

PRICING_MODELS = {
    "free",
    "freemium",
    "subscription",
    "one-time",
    "unknown",
    "varies",
}

def clean_metadata_text(value):
    """Decode HTML entities and remove markup in publisher/search snippets."""
    if not isinstance(value, str):
        return None
    text = value
    for _ in range(3):
        decoded = html.unescape(text)
        if decoded == text:
            break
        text = decoded
    # Remove actual HTML tags, but preserve ordinary angle-bracketed text.
    text = re.sub(r"</?[A-Za-z][A-Za-z0-9:-]*(?:\s+[^<>]*?)?\s*/?>", " ", text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return normalize_whitespace(text)

def normalize_whitespace(value):
    if value is None:
        return None

    return " ".join(value.split())

# ADDED as part of issue #32 resolution:
# Accept only classifications supported by the current database schema.
# Preserve None when classification evidence is unavailable.
def normalize_classification(value, allowed_values):
    """Return a valid classification or None."""

    if value is None:
        return None

    if value in allowed_values:
        return value

    return None

# UPDATED as part of issue #32 resolution:
# Normalize resource metadata using database-compatible classifications.
# Preserve the existing dictionary keys required by the Django frontend.
def create_resource(
        title,
        url,
        source=None,
        creator=None,
        resource_format=None,
        resource_type=None,
        duration_seconds=None,
        description=None,
        views=None,
        likes=None,
        upload_date=None,
        pricing_model=None,
        difficulty=None,
):
    """Create a normalized resource dictionary for discovery results."""
    normalized_type = normalize_classification(
        resource_type,
        RESOURCE_TYPES,
    )

    normalized_format = normalize_classification(
        resource_format,
        RESOURCE_FORMATS,
    )

    normalized_pricing = normalize_classification(
        pricing_model,
        PRICING_MODELS,
    )

    return {
        "title": normalize_whitespace(title),
        "url": url,
        "source": source,
        "creator": normalize_whitespace(creator),
        "resource_format": normalized_format,
        "resource_type": normalized_type,
        "description": clean_metadata_text(description),
        "duration_seconds": duration_seconds,
        "views": views,
        "likes": likes,
        "upload_date": upload_date,
        "pricing_model": normalized_pricing,
        "difficulty": difficulty if difficulty in {"Beginner", "Intermediate", "Advanced"} else None,
    }
