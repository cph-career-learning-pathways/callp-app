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
)
from .resource_normalizer import create_resource
from .discovery_filters import build_discovery_query
from .youtube_parser import (
    extract_youtube_metadata,
    get_youtube_resource_type,
)

# GLOBAL CONSTANTS

SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
SEARCH_API_CANDIDATES = 20
RESOURCE_REQUEST_TIMEOUT = 10
MAX_INSPECTION_WORKERS = 5


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
            }
        )

    return candidates


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
        return None

    content_type = resource_response.headers.get("Content-Type", "")

    if "text/html" not in content_type:
        return None

    soup = BeautifulSoup(resource_response.content, "html.parser")

    hostname = urlparse(url).hostname

    if hostname and hostname.startswith("www."):
        hostname = hostname[4:]

    og_title = soup.find("meta", property="og:title")
    og_description = soup.find("meta", property="og:description")

    title = (
        og_title.get("content")
        if og_title and og_title.get("content")
        else candidate.get("title")
    )

    description = (
        og_description.get("content")
        if og_description and og_description.get("content")
        else None
    )

    json_ld_types = extract_json_ld_types(soup)

    if "youtube.com" in url:
        youtube_type = get_youtube_resource_type(url)

        if youtube_type == "video":
            youtube_metadata = extract_youtube_metadata(soup)

            return create_resource(
                title=title,
                url=url,
                source="YouTube",
                creator=youtube_metadata["channel"],
                resource_format="video",
                resource_type=None,
                description=description,
                duration_seconds=youtube_metadata["duration_seconds"],
                views=youtube_metadata["view_count"],
                likes=youtube_metadata["like_count"],
                upload_date=youtube_metadata["upload_date"],
                pricing_model=None,
            )

        # Playlist-specific normalization has not been implemented yet.
        return None

    page_text = extract_page_text(soup)

    resource_type = classify_resource_type(json_ld_types)

    pricing_model = classify_pricing_model(
        title=title,
        description=description,
        page_text=page_text,
        json_ld_types=json_ld_types,
    )

    return create_resource(
        title=title,
        url=url,
        source=hostname,
        creator=None,
        resource_format="webpage",
        resource_type=resource_type,
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
            if resource is not None
        ]

    return resources


def main():
    query = input("Search: ")
    resources = search_resources(query)

    print(f"\nNormalized resources ({len(resources)}):")

    for number, resource in enumerate(resources, start=1):
        print(f"\n{number}). {resource}")


if __name__ == "__main__":
    main()
