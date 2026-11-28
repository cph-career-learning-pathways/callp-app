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

    free_tutorial_pattern = re.search(
        r"\bfree\b(?:\s+[\w-]+){0,3}\s+\btutorial\b", combined_text
    )
    if free_course_pattern or free_tutorial_pattern:
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

    # Site-wide body text often contains unrelated subscription offers and ads.
    # Never infer the resource's price from arbitrary page text.
    # Explicit resource title/description or structured offers are required.
    evidence = primary_evidence

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

def classify_difficulty(title=None, description=None, learning_resource_type=None):
    """Classify only explicit resource-level difficulty evidence."""
    text = " ".join(str(v) for v in (title, description) if isinstance(v, str))
    if isinstance(learning_resource_type, str):
        text += " " + learning_resource_type
    text = text.casefold()
    matches = set()
    if re.search(r"\b(beginner|beginners|introductory|introduction|fundamentals|novice)\b", text):
        matches.add("Beginner")
    if re.search(r"\bintermediate\b", text):
        matches.add("Intermediate")
    if re.search(r"\badvanced\b", text):
        matches.add("Advanced")
    return next(iter(matches)) if len(matches) == 1 else None


def classify_structured_pricing(objects):
    """Read explicit offer prices; avoid guessing from generic page copy."""
    prices = []
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        offers = obj.get("offers")
        if isinstance(offers, dict):
            offers = [offers]
        if not isinstance(offers, list):
            continue
        for offer in offers:
            if not isinstance(offer, dict):
                continue
            price = offer.get("price")
            if price is None:
                price = (offer.get("priceSpecification") or {}).get("price") if isinstance(offer.get("priceSpecification"), dict) else None
            try:
                prices.append(float(str(price).replace(",", "")))
            except (ValueError, TypeError):
                pass
    if not prices:
        return None
    if any(v < 0 for v in prices):
        return None
    if all(v == 0 for v in prices):
        return "free"
    if all(v > 0 for v in prices):
        return None  # A price alone does not establish a one-time purchase.
    return "varies"


def classify_youtube_resource_type(title=None, description=None):
    """Classify explicit instructional courses/tutorials; otherwise stay unknown.

    Do not infer a course from duration, the hosting platform, or generic
    educational keywords such as 'learn' or 'lesson'.
    """
    title_text = title.strip() if isinstance(title, str) else ""
    description_text = description.strip() if isinstance(description, str) else ""
    if re.search(r"\b(full|complete|entire)\s+(?:[\w-]+\s+){0,3}course\b|\b(?:full|complete)\s+(?:[\w-]+\s+){0,3}tutorial\b|\b(?:course|tutorial)\s+(?:[\w-]+\s+){0,3}(?:for beginners|from scratch)\b", title_text, re.I):
        return "course"
    if re.search(r"\b(?:full|complete)\s+(?:[\w-]+\s+){0,3}course\b", description_text, re.I):
        return "course"
    return None
