import json
import os

import requests

from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse

from .resource_classifier import (
    classify_pricing_model,
    classify_resource_type,
    classify_difficulty,
    classify_structured_pricing,
    classify_youtube_resource_type,
)
from .resource_normalizer import create_resource
from .discovery_filters import build_discovery_query, normalize_filters
from .youtube_parser import (
    extract_youtube_metadata,
    get_youtube_resource_type,
)

# GLOBAL CONSTANTS

SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
SEARCH_API_CANDIDATES = 20
RESOURCE_REQUEST_TIMEOUT = 10
MAX_INSPECTION_WORKERS = 8


# HELPER FUNCTIONS

def iter_json_ld_objects(value):
    if isinstance(value, dict):
        yield value

        graph = value.get("@graph")

        if isinstance(graph, list):
            for item in graph:
                yield from iter_json_ld_objects(item)

    elif isinstance(value, list):
        for item in value:
            yield from iter_json_ld_objects(item)


def get_api_key():
    load_dotenv()

    api_key = os.getenv("BRAVE_SEARCH_API_KEY")

    if not api_key:
        raise RuntimeError("BRAVE_SEARCH_API_KEY was not found.")

    return api_key


def search_brave(query):
    headers = {
        "X-Subscription-Token": get_api_key(),
        "Accept": "application/json",
    }

    params = {
        "q": query,
        "count": SEARCH_API_CANDIDATES,
        "country": "US",
        "search_lang": "en",
        "ui_lang": "en-US",
    }

    response = requests.get(
        SEARCH_URL,
        headers=headers,
        params=params,
        timeout=RESOURCE_REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()
    raw_results = data.get("web", {}).get("results", [])

    candidates = []

    for result in raw_results:
        candidates.append(
            {
                "title": result.get("title"),
                "url": result.get("url"),
                "description": result.get("description"),
            }
        )

    return candidates


def extract_json_ld_description(soup):
    """Find the first resource-level description in structured metadata."""
    for block in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(block.get_text(strip=True))
        except (ValueError, TypeError):
            continue
        for item in iter_json_ld_objects(data):
            description = item.get("description")
            if isinstance(description, str) and description.strip():
                return description.strip()
    return None


def extract_json_ld_types(soup):
    json_ld_blocks = soup.find_all(
        "script",
        type="application/ld+json",
    )

    json_ld_types = []

    for block in json_ld_blocks:
        try:
            structured_data = json.loads(block.get_text(strip=True))
        except json.JSONDecodeError:
            continue

        for item in iter_json_ld_objects(structured_data):
            item_type = item.get("@type")

            if isinstance(item_type, list):
                json_ld_types.extend(item_type)
            elif item_type:
                json_ld_types.append(item_type)

    return json_ld_types


def extract_structured_objects(soup):
    objects = []
    for block in soup.find_all("script", type="application/ld+json"):
        try:
            objects.extend(iter_json_ld_objects(json.loads(block.get_text(strip=True))))
        except (ValueError, TypeError):
            continue
    return objects


def _schema_type_names(types):
    return {str(t).rstrip("/").rsplit("/", 1)[-1].rsplit("#", 1)[-1]
            for t in types if isinstance(t, str)}


def classify_page_format(soup, json_ld_types, url, content_type):
    """Classify the primary resource, not supplementary embedded media.

    A VideoObject on an Article/BlogPosting page may describe an embedded clip.
    A dedicated video page must provide video-specific primary-page evidence.
    """
    mime = (content_type or "").split(";", 1)[0].strip().lower()
    path = urlparse(url).path.lower()
    if mime == "application/pdf" or path.endswith(".pdf"):
        return "document"
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("audio/"):
        return None  # No audio value in the current database schema.

    types = _schema_type_names(json_ld_types)
    article_types = {"Article", "NewsArticle", "BlogPosting", "TechArticle",
                     "ScholarlyArticle"}
    if types & article_types:
        return "webpage"

    if soup is None:
        return "webpage"

    og_type = soup.find("meta", attrs={"property": "og:type"})
    og_value = (og_type.get("content") or "").strip().casefold() if og_type else ""
    if og_value.startswith("video.") or og_value == "video":
        return "video"

    # VideoObject alone is insufficient: many text tutorials embed videos.
    # Require a dedicated video URL and structured video metadata together.
    path_segments = [part for part in path.split("/") if part]
    dedicated_video_path = any(part in {"video", "videos", "watch"}
                               for part in path_segments)
    if "VideoObject" in types and dedicated_video_path:
        return "video"
    return "webpage"


def build_search_query_for_filters(query, normalized_filters):
    """Prefer video candidates for video-only searches; still validate results."""
    selected_formats = {str(value).strip().casefold()
                        for value in normalized_filters["formats"]}
    if selected_formats == {"video"}:
        return f"{query} video".strip()
    return query


def extract_page_text(soup):
    main_tag = soup.find("main")
    article_tag = soup.find("article")
    role_main = soup.find(attrs={"role": "main"})

    if main_tag is not None:
        content = main_tag
    elif article_tag is not None:
        content = article_tag
    elif role_main is not None:
        content = role_main
    else:
        content = soup

    for tag in content(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    return content.get_text(
        separator=" ",
        strip=True,
    )


def fallback_resource(candidate):
    """Preserve a search result when the publisher cannot be inspected."""
    url = candidate.get("url")
    if not url:
        return None
    hostname = (urlparse(url).hostname or "").removeprefix("www.")
    return create_resource(
        title=candidate.get("title"), url=url, source=hostname,
        description=candidate.get("description"),
    )


def canonical_source(value):
    """Normalize known provider labels and exact hostnames, not substrings."""
    if value is None:
        return None
    name = str(value).strip().casefold()
    if name in {"youtube", "youtube.com", "www.youtube.com", "m.youtube.com"}:
        return "youtube"
    if name.startswith("www."):
        return name[4:]
    return name


def matches_discovery_filters(resource, filters):
    """Strict matching for fields that normalized web results actually expose.

    Unknown values never satisfy an explicitly selected filter. Skill, degree,
    and career intent currently influence the search query only; no authoritative
    per-result tags are available for those categories.
    """
    field_mapping = {
        "prices": "pricing_model", "sources": "source",
        "resource_types": "resource_type", "formats": "resource_format",
        "difficulties": "difficulty",
    }
    for filter_name, field_name in field_mapping.items():
        selected = {str(value).casefold().strip() for value in filters[filter_name]}
        if not selected:
            continue
        actual = resource.get(field_name)
        if filter_name == "sources":
            selected = {canonical_source(value) for value in selected}
            actual = canonical_source(actual)
        elif actual is not None:
            actual = str(actual).casefold().strip()
        if filter_name == "prices" and actual is None and "free" in selected:
            # Free discovery includes unknown pricing, but never known paid pricing.
            continue
        if actual is None or actual not in selected:
            return False
    return True


def inspect_resource(candidate):
    url = candidate.get("url")

    if not url:
        return None

    try:
        resource_response = requests.get(
            url,
            timeout=RESOURCE_REQUEST_TIMEOUT,
        )
        resource_response.raise_for_status()
    except requests.RequestException:
        return fallback_resource(candidate)

    content_type = resource_response.headers.get("Content-Type", "")

    if "text/html" not in content_type:
        fallback = fallback_resource(candidate)
        if fallback is not None:
            fallback["resource_format"] = classify_page_format(
                None, [], url, content_type
            ) if "application/pdf" in content_type.lower() or "video/" in content_type.lower() else None
        return fallback

    soup = BeautifulSoup(resource_response.content, "html.parser")

    hostname = urlparse(url).hostname

    if hostname and hostname.startswith("www."):
        hostname = hostname[4:]

    # UPDATED as part of issue #32 resolution:
    # Prefer Open Graph metadata while retaining Brave's title fallback.
    # Use the standard HTML description when Open Graph is unavailable.
    og_title = soup.find("meta", property="og:title")
    og_description = soup.find("meta", property="og:description")
    meta_description = soup.find("meta", attrs={"name": "description"})

    title = (
        og_title.get("content")
        if og_title and og_title.get("content")
        else candidate.get("title")
    )

    description = None

    if og_description and og_description.get("content"):
        description = og_description.get("content").strip()

    elif meta_description and meta_description.get("content"):
        description = meta_description.get("content").strip()

    if not description:
        description = extract_json_ld_description(soup) or candidate.get("description")

    json_ld_types = extract_json_ld_types(soup)
    structured_objects = extract_structured_objects(soup)

    # UPDATED as part of issue #32 resolution:
    #   Validate the hostname to prevent unrelated domains from
    #   being incorrectly identified as YouTube resources.
    if hostname and (
        hostname == "youtube.com"
        or hostname.endswith(".youtube.com")
    ):
        youtube_type = get_youtube_resource_type(url)

        if youtube_type == "video":
            youtube_metadata = extract_youtube_metadata(soup)
            # Video-specific player metadata is preferable to site-wide OG copy.
            youtube_description = youtube_metadata.get("description") or description

            return create_resource(
                title=title,
                url=url,
                source="YouTube",
                creator=youtube_metadata["channel"],
                resource_format="video",
                resource_type=classify_youtube_resource_type(title, youtube_description),
                description=youtube_description,
                duration_seconds=youtube_metadata["duration_seconds"],
                views=youtube_metadata["view_count"],
                likes=youtube_metadata["like_count"],
                upload_date=youtube_metadata["upload_date"],
                pricing_model=youtube_metadata["pricing_model"],
                difficulty=classify_difficulty(title, youtube_description),
            )

        # Playlist-specific normalization has not been implemented yet.
        return None

    page_text = extract_page_text(soup)

    resource_type = classify_resource_type(json_ld_types)
    learning_type = next((obj.get("learningResourceType") for obj in structured_objects
                          if isinstance(obj.get("learningResourceType"), str)), None)
    difficulty = classify_difficulty(title, description, learning_type)
    resource_format = classify_page_format(soup, json_ld_types, url, content_type)

    pricing_model = classify_pricing_model(
        title=title,
        description=description,
        page_text=page_text,
        json_ld_types=json_ld_types,
    )

    structured_pricing = classify_structured_pricing(structured_objects)
    if structured_pricing is not None:
        pricing_model = structured_pricing

    return create_resource(
        title=title,
        url=url,
        source=hostname,
        creator=None,
        resource_format=resource_format,
        resource_type=resource_type,
        difficulty=difficulty,
        description=description,
        duration_seconds=None,
        views=None,
        likes=None,
        upload_date=None,
        pricing_model=pricing_model,
    )

def search_resources(query="", filters=None):
    """Search Brave and inspect candidate webpages concurrently."""
    discovery_query = build_discovery_query(
        query=query,
        filters=filters,
    )

    if not discovery_query:
        return []

    normalized_filters = normalize_filters(filters)
    discovery_query = build_search_query_for_filters(
        discovery_query, normalized_filters
    )
    candidates = search_brave(discovery_query)

    if not candidates:
        return []

    worker_count = min(MAX_INSPECTION_WORKERS, len(candidates))

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        inspected_resources = executor.map(
            inspect_resource,
            candidates,
        )

        resources = [
            resource
            for resource in inspected_resources
            if resource is not None and matches_discovery_filters(
                resource, normalized_filters
            )
        ]

    # Confirmed-free results first; retain Brave order within each group.
    if "free" in {str(v).strip().casefold() for v in normalized_filters["prices"]}:
        resources.sort(key=lambda resource: resource.get("pricing_model") is None)

    return resources


def main():
    query = input("Search: ")
    resources = search_resources(query)

    print(f"\nNormalized resources ({len(resources)}):")

    for number, resource in enumerate(resources, start=1):
        print(f"\n{number}). {resource}")


if __name__ == "__main__":
    main()
