"""Query helpers for the unmanaged career-resource schema in models.py."""

from django.db.models import Count, Q, Prefetch

from .models import (
    Category, CuratedCollection, Filter, PriceModel, CareerResource,
    Source, CollectionResources, ResourceCategory,
)

LAST_COLLECTION_SEARCH = "last_collection_search"
LAST_WEB_SEARCH = "last_web_search"


def format_duration(seconds):
    if seconds is None:
        return None
    if seconds < 60:
        return "Less than a minute"
    minutes = round(seconds / 60)
    if minutes < 60:
        return f"{minutes} min"
    hours = seconds / 3600
    return f"{int(hours)} hr" if hours.is_integer() else f"{hours:.1f} hr"


def get_filter_options():
    active_categories = Category.objects.filter(is_active="Y")
    return {
        "skill_options": active_categories.filter(category_type="skill").order_by("category_name"),
        "degree_program_options": active_categories.filter(category_type="degree program").order_by("category_name"),
        "career_field_options": active_categories.filter(category_type="career field").order_by("category_name"),
        "price_options": PriceModel.objects.filter(is_active="Y").order_by("price_model_name"),
        "source_options": Source.objects.filter(is_active="Y").order_by("source_name"),
        "resource_type_options": CareerResource.objects.filter(is_active="Y").exclude(resource_type="").values_list("resource_type", flat=True).distinct().order_by("resource_type"),
        "resource_format_options": CareerResource.objects.filter(is_active="Y").exclude(resource_format="").values_list("resource_format", flat=True).distinct().order_by("resource_format"),
        "difficulty_options": Filter.objects.filter(is_active="Y", filter_type__iexact="difficulty").order_by("filter_name"),
    }


def apply_collection_filters(collections, selected_skills, selected_degree_programs,
                             selected_career_fields, selected_prices, selected_sources,
                             selected_resource_types, selected_formats, selected_difficulties):
    """OR within a filter group; AND between groups, via explicit join models."""
    category_path = "collection_resources__resource__resource_categories__category"
    for values, category_type in (
        (selected_skills, "skill"),
        (selected_degree_programs, "degree program"),
        (selected_career_fields, "career field"),
    ):
        if values:
            collections = collections.filter(**{
                f"{category_path}__category_type": category_type,
                f"{category_path}__category_name__in": values,
                f"{category_path}__is_active": "Y",
                "collection_resources__resource__is_active": "Y",
            })

    resource_path = "collection_resources__resource"
    for values, lookup in (
        (selected_prices, "price_model__price_model_name__in"),
        (selected_sources, "source__source_name__in"),
        (selected_resource_types, "resource_type__in"),
        (selected_formats, "resource_format__in"),
    ):
        if values:
            collections = collections.filter(**{
                f"{resource_path}__{lookup}": values,
                f"{resource_path}__is_active": "Y",
            })
    if selected_difficulties:
        collections = collections.filter(**{
            f"{resource_path}__resource_filters__filter__filter_name__in": selected_difficulties,
            f"{resource_path}__resource_filters__filter__filter_type__iexact": "difficulty",
            f"{resource_path}__resource_filters__filter__is_active": "Y",
            f"{resource_path}__is_active": "Y",
        })
    return collections.distinct()


def _collection_queryset():
    active_categories = ResourceCategory.objects.select_related("category").filter(category__is_active="Y")
    resources = CareerResource.objects.filter(is_active="Y").prefetch_related(
        Prefetch("resource_categories", queryset=active_categories)
    )
    links = CollectionResources.objects.select_related("resource").filter(
        resource__is_active="Y"
    ).order_by("sort_order").prefetch_related(
        Prefetch("resource__resource_categories", queryset=active_categories)
    )
    return CuratedCollection.objects.filter(is_active="Y").prefetch_related(
        Prefetch("collection_resources", queryset=links)
    ).annotate(resource_count=Count(
        "collection_resources__resource", filter=Q(collection_resources__resource__is_active="Y"), distinct=True
    ))


def prepare_collection_cards(collections):
    collections = list(collections)
    for collection in collections:
        names, seen = [], set()
        for link in collection.collection_resources.all():
            for category_link in link.resource.resource_categories.all():
                name = category_link.category.category_name
                if name not in seen:
                    seen.add(name)
                    names.append(name)
        collection.display_categories = names[:4]
    return collections


def search_local_collections(search_query, selected_skills, selected_degree_programs,
                             selected_career_fields, selected_prices, selected_sources,
                             selected_resource_types, selected_formats, selected_difficulties):
    collections = _collection_queryset()
    if search_query:
        collections = collections.filter(
            Q(collection_name__icontains=search_query) |
            Q(collection_description__icontains=search_query)
        )
    collections = apply_collection_filters(
        collections, selected_skills, selected_degree_programs, selected_career_fields,
        selected_prices, selected_sources, selected_resource_types, selected_formats,
        selected_difficulties,
    )
    return prepare_collection_cards(collections.order_by("collection_name"))


def restore_local_collections(collection_ids):
    if not collection_ids:
        return []
    collections = _collection_queryset().filter(collection_id__in=collection_ids)
    by_id = {item.collection_id: item for item in collections}
    return prepare_collection_cards([by_id[item_id] for item_id in collection_ids if item_id in by_id])


def search_web_resources(
    search_query,
    selected_skills,
    selected_degree_programs,
    selected_career_fields,
    ):
    """Discover external learning resources without saving them to MySQL."""

    from resource_discovery.search import search_resources

    filters = {
        "skills": selected_skills,
        "degree_programs": selected_degree_programs,
        "career_fields": selected_career_fields,
    }

    resources = search_resources(
        query=search_query,
        filters=filters,
    )

    for resource in resources:
        duration_seconds = resource.get("duration_seconds")

        resource["display_duration"] = None

        if duration_seconds is not None:
            minutes = round(duration_seconds / 60)

            if minutes < 60:
                resource["display_duration"] = f"{minutes} min"
            else:
                hours, remaining_minutes = divmod(minutes, 60)

                if remaining_minutes:
                    resource["display_duration"] = (
                        f"{hours} hr {remaining_minutes} min"
                    )
                else:
                    resource["display_duration"] = f"{hours} hr"

    return resources

def build_search_state(search_query, selected_skills, selected_degree_programs,
                       selected_career_fields, selected_prices, selected_sources,
                       selected_resource_types, selected_formats, selected_difficulties):
    return {
        "query": search_query,
        "skills": list(selected_skills),
        "degree_programs": list(selected_degree_programs),
        "career_fields": list(selected_career_fields),
        "prices": list(selected_prices),
        "sources": list(selected_sources),
        "resource_types": list(selected_resource_types),
        "formats": list(selected_formats),
        "difficulties": list(selected_difficulties),
    }

# Added as part of issue #32 resolution:
#   Retrieve the selected search criteria from the current request or
#   from a previously cached search in the user's session.
def get_search_state(request, cached_search=None):
    """Return search criteria in a consistent dictionary structure."""

    if cached_search is not None:
        return {
            "query": cached_search.get("query", ""),
            "skills": cached_search.get("skills", []),
            "degree_programs": cached_search.get("degree_programs", []),
            "career_fields": cached_search.get("career_fields", []),
            "prices": cached_search.get("prices", []),
            "sources": cached_search.get("sources", []),
            "resource_types": cached_search.get("resource_types", []),
            "formats": cached_search.get("formats",[]),
            "difficulties": cached_search.get("difficulties", []),
        }

    return{
        "query": request.GET.get("search", "").strip(),
        "skills": request.GET.getlist("skill"),
        "degree_programs": request.GET.getlist("degree_program"),
        "career_fields": request.GET.getlist("career_field"),
        "prices": request.GET.getlist("price"),
        "sources": request.GET.getlist("source"),
        "resource_types": request.GET.getlist("resource_type"),
        "formats": request.GET.getlist("format"),
        "difficulties": request.GET.getlist("difficulty"),
    }

# Added as part of issue #32 resolution:
#   Build the common template for Collections and Resource Discovery.
#   Preserve the previous-search button using the existing session keys.
def build_search_context(request, search_state, search_mode):
    """Return shared filter, search, and navigation context"""

    if search_mode == "web":
        has_previous_search = (
            LAST_COLLECTION_SEARCH in request.session
        )

        if has_previous_search:
            swap_target = "collections"
            swap_label = "Last Collection Search"
        else:
            swap_target = None
            swap_label = None

    else:
        has_previous_search = LAST_WEB_SEARCH in request.session

        if has_previous_search:
            swap_target = "web"
            swap_label = "Last Web Search"
        else:
            swap_target = None
            swap_label = None

    context = {
        "search_query": search_state["query"],
        "selected_skills": search_state["skills"],
        "selected_degree_programs": search_state["degree_programs"],
        "selected_career_fields": search_state["career_fields"],
        "selected_prices": search_state["prices"],
        "selected_sources": search_state["sources"],
        "selected_resource_types": search_state["resource_types"],
        "selected_formats": search_state["formats"],
        "selected_difficulties": search_state["difficulties"],
        "search_mode": search_mode,
        "swap_target": swap_target,
        "swap_label": swap_label,
        **get_filter_options(),
    }

    return context