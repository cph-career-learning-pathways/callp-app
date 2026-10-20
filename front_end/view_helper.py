from .models import (
    Category,
    CuratedCollection,
    Filter,
    PriceModel,
    CareerResource,
    Source,
)

def format_duration(seconds):
    """Convert a duration in seconds into a compact display string."""
    if seconds is None:
        return None
    if seconds < 60:
        return "Less than a minute"

    minutes = round(seconds / 60)
    if minutes < 60:
        return f"{minutes} min"

    hours = seconds / 3600
    if hours.is_integer():
        return f"{int(hours)} hr"

    return f"{hours:.1f} hr"


def get_filter_options():
    """Load all filter options used by the topbar and left sidebar."""

    return {
        # Category taxonomy
        "skill_options": Category.objects.filter(
            category_type="Skill",
            is_active=True,
        ).order_by("category_name"),

        "degree_program_options": Category.objects.filter(
            category_type="Degree Program",
            is_active=True,
        ).order_by("category_name"),

        "career_field_options": Category.objects.filter(
            category_type="Career Field",
            is_active=True,
        ).order_by("category_name"),

        # Price
        "price_options": PriceModel.objects.filter(
            is_active=True,
        ).order_by("price_model_name"),

        # Sources
        "source_options": Source.objects.filter(
            is_active=True,
        ).order_by("source_name"),

        # Resource fields
        "resource_type_options": (
            Resource.objects
            .exclude(resource_type__isnull=True)
            .exclude(resource_type="")
            .values_list("resource_type", flat=True)
            .distinct()
            .order_by("resource_type")
        ),

        "resource_format_options": (
            Resource.objects
            .exclude(resource_format__isnull=True)
            .exclude(resource_format="")
            .values_list("resource_format", flat=True)
            .distinct()
            .order_by("resource_format")
        ),

        # ResourceFilter / Filter model
        "difficulty_options": Filter.objects.filter(
            is_active=True,
        ).order_by("filter_name"),
    }


def apply_collection_filters(
    collections,
    selected_skills,
    selected_degree_programs,
    selected_career_fields,
    selected_prices,
    selected_sources,
    selected_resource_types,
    selected_formats,
    selected_difficulties,
):
    """
    Apply all sidebar filters to collections.

    Multiple values within one filter group use OR behavior.
    Different filter groups use AND behavior.
    """

    if selected_skills:
        collections = collections.filter(
            resources__categories__category_type="Skill",
            resources__categories__category_name__in=selected_skills,
        )

    if selected_degree_programs:
        collections = collections.filter(
            resources__categories__category_type="Degree Program",
            resources__categories__category_name__in=selected_degree_programs,
        )

    if selected_career_fields:
        collections = collections.filter(
            resources__categories__category_type="Career Field",
            resources__categories__category_name__in=selected_career_fields,
        )

    if selected_prices:
        collections = collections.filter(
            resources__price_model__price_model_name__in=selected_prices,
        )

    if selected_sources:
        collections = collections.filter(
            resources__source__source_name__in=selected_sources,
        )

    if selected_resource_types:
        collections = collections.filter(
            resources__resource_type__in=selected_resource_types,
        )

    if selected_formats:
        collections = collections.filter(
            resources__resource_format__in=selected_formats,
        )

    if selected_difficulties:
        collections = collections.filter(
            resources__resourcefilter__filter__filter_name__in=selected_difficulties,
        )

    return collections.distinct()


def prepare_collection_cards(collections):
    """Add compact preview data used by the stacked collection cards."""
    collections = list(collections)

    for collection in collections:
        # ADDED: Show a small taxonomy preview without duplicating every category
        # present in the collection. The full collection detail view can expose
        # more later when that route is implemented.
        category_names = []
        seen_names = set()

        for resource in collection.resources.all():
            for category in resource.categories.all():
                if category.category_name not in seen_names:
                    seen_names.add(category.category_name)
                    category_names.append(category.category_name)

        collection.display_categories = category_names[:4]

    return collections


def search_local_collections(
    search_query,
    selected_skills,
    selected_degree_programs,
    selected_career_fields,
    selected_prices,
    selected_sources,
    selected_resource_types,
    selected_formats,
    selected_difficulties,
):
    """Return active CuratedCollection objects for Collections mode.

    ADDED: Collections mode now renders one card per collection rather than
    flattening matching collections into individual Resource cards. This makes
    the stacked-card presentation semantically represent a group of resources.
    """
    collections = (
        CuratedCollection.objects
        .filter(is_active=True)
        .prefetch_related("resources__categories")
    )

    if search_query:
        collections = collections.filter(
            Q(collection_name__icontains=search_query)
            | Q(collection_description__icontains=search_query)
        )

    collections = apply_collection_filters(
        collections,
        selected_skills,
        selected_degree_programs,
        selected_career_fields,
        selected_prices,
        selected_sources,
        selected_resource_types,
        selected_formats,
        selected_difficulties,
    )

    collections = (
        collections
        .annotate(resource_count=Count("resources", distinct=True))
        .distinct()
        .order_by("collection_name")
    )

    return prepare_collection_cards(collections)

def restore_local_collections(collection_ids):
    """Restore cached Collections results using inexpensive local IDs."""
    if not collection_ids:
        return []

    collections = (
        CuratedCollection.objects
        .filter(collection_id__in=collection_ids, is_active=True)
        .prefetch_related("resources__categories")
        .annotate(resource_count=Count("resources", distinct=True))
    )

    collections_by_id = {
        collection.collection_id: collection
        for collection in collections
    }

    ordered_collections = [
        collections_by_id[collection_id]
        for collection_id in collection_ids
        if collection_id in collections_by_id
    ]

    return prepare_collection_cards(ordered_collections)


def search_web_resources(
    search_query,
    selected_skills,
    selected_degree_programs,
    selected_career_fields,
):
    """Call Resource Discovery and return transient normalized dictionaries."""
    discovery_filters = {
        "skills": selected_skills,
        "degree_programs": selected_degree_programs,
        "career_fields": selected_career_fields,
    }

    results = search_resources(
        search_query,
        filters=discovery_filters,
    )

    for result in results:
        result["display_duration"] = format_duration(
            result.get("duration_seconds")
        )

    return results


def build_search_state(
    search_query,
    selected_skills,
    selected_degree_programs,
    selected_career_fields,
    selected_prices,
    selected_sources,
    selected_resource_types,
    selected_formats,
    selected_difficulties,
):
    """Return the serializable form state shared by both cached search modes."""
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

