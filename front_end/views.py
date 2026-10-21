from django.shortcuts import render, redirect
from django.urls import reverse
from .models import CareerResource
from .view_helper import (
    LAST_COLLECTION_SEARCH, LAST_WEB_SEARCH, get_filter_options,
    restore_local_collections, search_local_collections, search_web_resources,
    build_search_state,
)

# Create your views here.
def index(request):
    # Existing behavior: swap_to restores the previous result set instead of
    # executing either search backend again.
    swap_to = request.GET.get("swap_to")
    if swap_to in {"collections", "web"}:
        session_key = (
            LAST_COLLECTION_SEARCH
            if swap_to == "collections"
            else LAST_WEB_SEARCH
        )
        cached_search = request.session.get(session_key)

        if cached_search:
            request.session["display_cached_search"] = {
                "mode": swap_to,
                "cache_key": session_key,
            }
            return redirect(reverse("index"))

    displayed_cache = request.session.pop("display_cached_search", None)
    cached_search = None

    if displayed_cache and not request.GET:
        search_mode = displayed_cache.get("mode", "collections")
        cached_search = request.session.get(displayed_cache.get("cache_key"))
    else:
        search_mode = request.GET.get("search_mode", "collections")

    if search_mode not in {"collections", "web"}:
        search_mode = "collections"

    if cached_search:
        search_query = cached_search.get("query", "")

        selected_skills = cached_search.get("skills", [])
        selected_degree_programs = cached_search.get("degree_programs", [])
        selected_career_fields = cached_search.get("career_fields", [])

        selected_prices = cached_search.get("prices", [])
        selected_sources = cached_search.get("sources", [])
        selected_resource_types = cached_search.get("resource_types", [])
        selected_formats = cached_search.get("formats", [])
        selected_difficulties = cached_search.get("difficulties", [])

    else:
        search_query = request.GET.get("search", "").strip()

        selected_skills = request.GET.getlist("skill")
        selected_degree_programs = request.GET.getlist("degree_program")
        selected_career_fields = request.GET.getlist("career_field")

        selected_prices = request.GET.getlist("price")
        selected_sources = request.GET.getlist("source")
        selected_resource_types = request.GET.getlist("resource_type")
        selected_formats = request.GET.getlist("format")
        selected_difficulties = request.GET.getlist("difficulty")

    filter_options = get_filter_options()

    collections = []
    discovery_results = []
    discovery_error = None

    has_discovery_intent = any(
        (
            selected_skills,
            selected_degree_programs,
            selected_career_fields,
        )
    )
    discovery_attempted = bool(search_query or has_discovery_intent)

    if search_mode == "web":
        if cached_search:
            # Reuse normalized Resource Discovery dictionaries. This performs no
            # Brave API request and no candidate-page scraping.
            discovery_results = cached_search.get("results", [])
            discovery_attempted = cached_search.get("attempted", True)
        elif discovery_attempted:
            try:
                discovery_results = search_web_resources(
                    search_query,
                    selected_skills,
                    selected_degree_programs,
                    selected_career_fields,
                )

                web_cache = build_search_state(                 
                    search_query,
                    selected_skills,
                    selected_degree_programs,
                    selected_career_fields,
                    selected_prices,
                    selected_sources,
                    selected_resource_types,
                    selected_formats,
                    selected_difficulties,
                )
                web_cache.update(
                    {
                        "results": discovery_results,
                        "attempted": True,
                    }
                )
                request.session[LAST_WEB_SEARCH] = web_cache
            except Exception as exc:
                discovery_error = f"Web resource search failed: {exc}"
    else:
        if cached_search:
            # UPDATED: Collections cache now stores collection IDs because the
            # Collections view renders collection cards rather than resources.
            collections = restore_local_collections(
                cached_search.get("collection_ids", [])
            )
        else:
            collections = search_local_collections(
                search_query,
                selected_skills,
                selected_degree_programs,
                selected_career_fields,
                selected_prices,
                selected_sources,
                selected_resource_types,
                selected_formats,
                selected_difficulties,
            )

            collection_cache = build_search_state(     
                search_query,
                selected_skills,
                selected_degree_programs,
                selected_career_fields,
                selected_prices,
                selected_sources,
                selected_resource_types,
                selected_formats,
                selected_difficulties,
            )
            collection_cache["collection_ids"] = [
                collection.collection_id
                for collection in collections
            ]
            request.session[LAST_COLLECTION_SEARCH] = collection_cache

    # Existing yellow swap button remains available only when the other mode has
    # a cached result set in this user's session.
    if search_mode == "web":
        swap_target = (
            "collections"
            if request.session.get(LAST_COLLECTION_SEARCH)
            else None
        )
        swap_label = "Last Collection Search" if swap_target else None
    else:
        swap_target = (
            "web"
            if request.session.get(LAST_WEB_SEARCH)
            else None
        )
        swap_label = "Last Web Search" if swap_target else None

    context = {
    "collections": collections,
    "collection_count": len(collections),
    "discovery_results": discovery_results,
    "discovery_count": len(discovery_results),
    "discovery_error": discovery_error,
    "discovery_attempted": discovery_attempted,

    "selected_skills": selected_skills,
    "selected_degree_programs": selected_degree_programs,
    "selected_career_fields": selected_career_fields,

    "selected_prices": selected_prices,
    "selected_sources": selected_sources,
    "selected_resource_types": selected_resource_types,
    "selected_formats": selected_formats,
    "selected_difficulties": selected_difficulties,

    "search_query": search_query,
    "search_mode": search_mode,
    "swap_target": swap_target,
    "swap_label": swap_label,

    **filter_options,
}

    return render(request, "front_end/index.html", context)


def resource_query(request):
    resources = CareerResource.objects.all()[:50]
    return render(request, "front_end/resource_query.html", {"resources": resources})
