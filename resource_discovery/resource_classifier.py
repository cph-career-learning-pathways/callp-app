import re

PRICING_EVIDENCE = {
    "explicit_free": [
        "free online course",
        "free course",
        "available for free",
        "at no cost",
        "no cost",
    ],

    "free_audit": [
        "free audit",
        "audit for free",
        "audit track",
    ],

    "limited_free": [
        "preview for free",
        "free preview",
        "first module free",
        "free lessons",
    ],

    "free_trial": [
        "free trial",
        "7-day free trial",
        "10-day free trial",
        "30-day free trial",
        "free month",
    ],

    "subscription": [
        "per month",
        "per year",
        "monthly subscription",
        "annual subscription",
        "active subscription",
        "subscription required",
        "become a member",
        "membership required",
    ],

    "one_time_purchase": [
        "one-time payment",
        "one time payment",
        "buy this course once",
        "once you purchase",
    ],

    "paywall": [
        "members-only",
        "members only",
        "member-only",
        "behind the paywall",
    ],
}

def collect_pricing_evidence(
    title=None,
    description=None,
    page_text=None,
):
    combined_text = " ".join(
        value
        for value in (title, description, page_text)
        if value
    )

    combined_text = " ".join(combined_text.split()).lower()

    evidence = {}

    for category, phrases in PRICING_EVIDENCE.items():
        evidence[category] = any(
            phrase in combined_text
            for phrase in phrases
        )

    free_course_pattern = re.search(
        r"\bfree\b(?:\s+\w+){0,3}\s+\bcourse\b",
        combined_text,
    )

    if free_course_pattern:
        evidence["explicit_free"] = True

    mixed_pricing_pattern = re.search(
        r"\bfree\b.{0,40}\bpaid\b|\bpaid\b.{0,40}\bfree\b",
        combined_text,
    )

    evidence["mixed_pricing"] = bool(mixed_pricing_pattern)

    return evidence

# UPDATED as part of issue #32 resolution:
#   Prioritize pricing evidence describing the resource itself.
#   Use webpage text only when the title and description provide
#   insufficient evidence, reducing unrelated pricing classifications.
def classify_pricing_model(
    title=None,
    description=None,
    page_text=None,
    json_ld_types=None,
):
    """Classify resource pricing using prioritized metadata evidence."""

    json_ld_types = json_ld_types or []

    # Prefer metadata describing the specific resource.
    primary_evidence = collect_pricing_evidence(
        title=title,
        description=description
    )

    is_collection = (
        "ItemList" in json_ld_types
        or "CollectionPage" in json_ld_types
    )

    has_primary_evidence = any(primary_evidence.values())

    if has_primary_evidence:
        evidence = primary_evidence

    else:
        # Use webpage text only when primary metadata is inconclusive.
        evidence = collect_pricing_evidence(
            page_text=page_text,
        )

    # Collections containing mixed access signals
    if is_collection:
        if evidence["mixed_pricing"]:
            return "varies"

        has_free_access = (
            evidence["explicit_free"]
            or evidence["free_audit"]
            or evidence["limited_free"]
        )

        has_paid_access = (
            evidence["free_trial"]
            or evidence["subscription"]
            or evidence["one_time_purchase"]
            or evidence["paywall"]
        )

        if has_free_access and has_paid_access:
            return "varies"

    # Subscription-required access
    if evidence["subscription"] or evidence["paywall"]:
        return "subscription"

    # Free trial implies eventual paid access
    if evidence["free_trial"]:
        return "subscription"

    # One-time purchase
    if evidence["one_time_purchase"]:
        return "one-time"

    # Partial/free-tier access
    if evidence["free_audit"] or evidence["limited_free"]:
        return "freemium"

    # Strong explicit free-resource evidence
    if evidence["explicit_free"]:
        return "free"

    return None

# UPDATED as part of issue #32 resolution:
#   Recognize additional Schema.org structured-data types while
#   preserving the resource classifications allowed by the database.
#   Return None when the available metadata is insufficient.
def classify_resource_type(json_ld_types):
    """Classify a resource using its JSON-LD structured-data types."""

    if not json_ld_types:
        return None

    course_types = {
        "Course",
    }

    article_types = {
        "Article",
        "NewsArticle",
        "BlogPosting",
        "TechArticle",
        "ScholarlyArticle",
    }

    collection_types = {
        "ItemList",
        "CollectionPage",
    }


    if any(item_type in course_types for item_type in json_ld_types):
        return "course"

    if any(item_type in article_types for item_type in json_ld_types):
        return "article"

    if any(item_type in collection_types for item_type in json_ld_types):
        return "collection"

    return None