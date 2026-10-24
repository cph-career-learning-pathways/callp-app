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
        "description": normalize_whitespace(description),
        "duration_seconds": duration_seconds,
        "views": views,
        "likes": likes,
        "upload_date": upload_date,
        "pricing_model": normalized_pricing,
    }
