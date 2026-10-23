import logging
from requests.exceptions import HTTPError

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse

from .models import (
    CareerResource,
    CuratedCollection,
    CollectionResources,
)

from .view_helper import (
    LAST_COLLECTION_SEARCH,
    LAST_WEB_SEARCH,
    restore_local_collections,
    search_local_collections,
    search_web_resources,
    build_search_state,
    get_search_state,
    build_search_context,
)

logger = logging.getLogger(__name__)

# Create your views here.

# UPDATED as part of issue #32 resolution:
#   Display and search curated collections stored in the CaLLP database.
#   Preserve collection filtering, session caching, and previous searches.
def index(request):
    """Display and search locally stored curated collections."""

    # Redirect to the previous Resource Discovery search when requested.
    if request.GET.get("swap_to") == "web":
        if LAST_WEB_SEARCH in request.session:
            return redirect(
                reverse("resource_discovery") + "?restore=1"
            )

    cached_search = None

    if request.GET.get("restore") == "1":
        cached_search = request.session.get(LAST_COLLECTION_SEARCH)

    search_state = get_search_state(request, cached_search)

    if cached_search is not None:
        # Restore the previous collection results without a new search
        collections = restore_local_collections(
            cached_search.get("collection_ids", [])
        )

    else:
        # Preserve the existing collection search and filtering behavior
        collections = search_local_collections(
            search_state["query"],
            search_state["skills"],
            search_state["degree_programs"],
            search_state["career_fields"],
            search_state["prices"],
            search_state["sources"],
            search_state["resource_types"],
            search_state["formats"],
            search_state["difficulties"],
        )

        collection_cache = build_search_state(
            search_state["query"],
            search_state["skills"],
            search_state["degree_programs"],
            search_state["career_fields"],
            search_state["prices"],
            search_state["sources"],
            search_state["resource_types"],
            search_state["formats"],
            search_state["difficulties"],
        )

        collection_cache["collection_ids"] = [
            collection.collection_id
            for collection in collections
        ]

        request.session[LAST_COLLECTION_SEARCH] = collection_cache

    context = build_search_context(request, search_state, "collections",)

    context.update({
        "collections": collections,
        "collection_count": len(collections),
    })

    return render(request, "front_end/index.html", context)

# ADDED as part of issue #32 resolution:
#   Display external learning resources discovered through Brave Search.
#   Restore previous results from the session without repeating API calls.
#   Discovered resources are not saved to the CaLLP database (will be in future).
def resource_discovery(request):
    """Search and display external learning resources"""

    # Redirect to the previous Collections search when requested.
    if request.GET.get("swap_to") == "collections":
        if LAST_COLLECTION_SEARCH in request.session:
            return redirect(
                reverse("index") + "?restore=1"
            )

    cached_search = None

    if request.GET.get("restore") == "1":
        cached_search = request.session.get(LAST_WEB_SEARCH)

    search_state = get_search_state(request, cached_search)

    discovery_results = []
    discovery_error = None

    has_discovery_intent = any((
        search_state["skills"],
        search_state["degree_programs"],
        search_state["career_fields"],
    ))

    discovery_attempted = bool(
        search_state["query"] or has_discovery_intent
    )

    if cached_search is not None:
        # Reuse previously normalized results from the user's session.
        discovery_results = cached_search.get("results", [])
        discovery_attempted = cached_search.get("attempted", True)

    elif discovery_attempted:
        try:
            discovery_results = search_web_resources(
                search_state["query"],
                search_state["skills"],
                search_state["degree_programs"],
                search_state["career_fields"],
            )

            web_cache = build_search_state(
                search_state["query"],
                search_state["skills"],
                search_state["degree_programs"],
                search_state["career_fields"],
                search_state["prices"],
                search_state["sources"],
                search_state["resource_types"],
                search_state["formats"],
                search_state["difficulties"],
            )

            web_cache.update({
                "results": discovery_results,
                "attempted": True,
            })

            request.session[LAST_WEB_SEARCH] = web_cache

        except HTTPError as exc:
            # Log the exception but display only its HTTP status code.
            logger.exception("Resource Discovery HTTP error")

            if exc.response is not None:
                discovery_error = (
                    "Web resource search failed: "
                    f"HTTP {exc.response.status_code}"
                )
            else:
                discovery_error = (
                    "Web resource search failed: HTTP error."
                )

        except Exception:
            # Do not expose internal Python exceptions to visitors.
            logger.exception("Resource Discovery search failed")

            discovery_error = (
                "Web resource search is temporarily unavailable. "
                "Please try again later."
            )

    context = build_search_context(request, search_state, "web")

    context.update({
        "discovery_results": discovery_results,
        "discovery_count": len(discovery_results),
        "discovery_error": discovery_error,
        "discovery_attempted": discovery_attempted,
    })

    return render(request, "front_end/resource_discovery.html", context,)

def collection_details(request, collection_id):
    # return curated collection and its details
    # used by rightbar for lazy loading
    collection = get_object_or_404(
        CuratedCollection,
        collection_id=collection_id,
        is_active="Y",
    )

    collection_resources = (
        CollectionResources.objects
        .filter(
            collection=collection,
            resource__is_active="Y",
        )
        .select_related(
            "resource",
            "resource__source",
            "resource__price_model",
        )
        .prefetch_related(
            "resource__resource_categories__category",
            "resource__resource_filters__filter",
        )
        .order_by("sort_order", "resource_id")
    )

    resources = []

    for association in collection_resources:
        resource = association.resource

        categories = [
            {
                "id": link.category.category_id,
                "name": link.category.category_name,
                "type": link.category.category_type,
            }
            for link in resource.resource_categories.all()
            if link.category.is_active == "Y"
        ]

        filters = [
            {
                "name": link.filter.filter_name,
                "type": link.filter.filter_type,
            }
            for link in resource.resource_filters.all()
            if link.filter.is_active == "Y"
        ]

        resources.append({
            "id": resource.resource_id,
            "title": resource.resource_title,
            "description": resource.resource_snippet or "",
            "url": resource.resource_url,
            "resource_type": resource.resource_type,
            "resource_format": resource.resource_format,
            "duration": resource.resource_duration,
            "publication_date": (
                resource.resource_pub_date.isoformat()
                if resource.resource_pub_date
                else None
            ),
            "source": (
                resource.source.source_name
                if resource.source
                else None
            ),
            "price_model": (
                resource.price_model.price_model_name
                if resource.price_model
                else None
            ),
            "categories": categories,
            "filters": filters,
        })

    return JsonResponse({
        "id": collection.collection_id,
        "name": collection.collection_name,
        "description": collection.collection_description or "",
        "resource_count": len(resources),
        "resources": resources,
    })

def resource_query(request):
    resources = CareerResource.objects.all()[:50]
    return render(request, "front_end/resource_query.html", {"resources": resources})