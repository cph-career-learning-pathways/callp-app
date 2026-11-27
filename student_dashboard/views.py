"""Real MySQL-backed student dashboard views and state-changing API."""
import json
import secrets
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Count, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from front_end.models import Account, CareerResource, CollectionResources, CuratedCollection, ResourceCategory
from .models import (
    LearningDay, PathwayProgressSummary, ResourceVisit, SavedResource,
    UserGamification, UserPathway, UserResourceProgress, XPTransaction,
)


def _account(request):
    return get_object_or_404(Account, auth_user=request.user)


def _resource_data(resource):
    return {
        "id": resource.resource_id,
        "title": resource.resource_title,
        "type": resource.resource_type,
        "description": resource.resource_snippet or "",
        "url": resource.resource_url,
    }


def _dt(value):
    return timezone.localtime(value).strftime("%b %d, %Y") if value else ""


def _streak(account):
    days = set(LearningDay.objects.filter(account=account).values_list("activity_date", flat=True))
    today = timezone.localdate()
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _recommendations(account, resource_ids):
    if not resource_ids:
        return []
    category_ids = list(ResourceCategory.objects.filter(resource_id__in=resource_ids)
                        .values_list("category_id", flat=True).distinct())
    if not category_ids:
        return []
    qs = (CareerResource.objects.filter(
        is_active="Y", resource_categories__category_id__in=category_ids)
        .exclude(resource_id__in=resource_ids)
        .exclude(saved_by__account=account)
        .annotate(relevance=Count("resource_categories__category_id", distinct=True))
        .order_by("-relevance", "resource_title").distinct()[:6])
    return [_resource_data(r) for r in qs]


@login_required
def dashboard_student(request):
    account = _account(request)
    saved = list(SavedResource.objects.filter(account=account).select_related("resource")
                 .order_by("-saved_at"))
    owned_collections = list(CuratedCollection.objects.filter(curator=account, is_active="Y")
                             .annotate(resource_count=Count("collection_resources"))
                             .order_by("-collection_add_date"))
    collection_ids = [c.collection_id for c in owned_collections]
    collection_entries = list(CollectionResources.objects.filter(collection_id__in=collection_ids)
                              .select_related("resource").order_by("sort_order"))
    resources_by_collection = {cid: [] for cid in collection_ids}
    for entry in collection_entries:
        resources_by_collection[entry.collection_id].append(_resource_data(entry.resource))

    visits = (ResourceVisit.objects.filter(account=account).select_related("resource")
              .order_by("-visited_at")[:100])
    visited = []
    visited_ids = set()
    for visit in visits:
        if visit.resource_id not in visited_ids:
            visited_ids.add(visit.resource_id)
            visited.append({**_resource_data(visit.resource), "when": _dt(visit.visited_at)})
        if len(visited) == 12:
            break

    progress = list(UserResourceProgress.objects.filter(account=account)
                    .select_related("resource").order_by("-updated_at"))
    latest_visits = {}
    for visit in ResourceVisit.objects.filter(
        account=account, resource_id__in=[p.resource_id for p in progress]
    ).order_by("-visited_at"):
        if visit.resource_id not in latest_visits:
            latest_visits[visit.resource_id] = visit.visited_at
        if len(latest_visits) >= len(progress):
            break

    pathway_rows = (UserPathway.objects.filter(account=account).select_related("collection")
                    .order_by("-started_at", "user_pathway_id"))
    # This view has no declared PK; it must be queried only, not written to.
    summaries = {s.user_pathway_id: s for s in
                 PathwayProgressSummary.objects.filter(account=account)}
    pathways = []
    for p in pathway_rows:
        summary = summaries.get(p.user_pathway_id)
        pathways.append({
            "id": p.user_pathway_id,
            "title": p.collection.collection_name,
            "description": p.collection.collection_description or "",
            "steps": int(summary.total_resources or 0) if summary else 0,
            "progress": float(summary.percent_complete or 0) if summary else 0,
            "status": p.pathway_status,
        })

    gamification = UserGamification.objects.filter(account=account).select_related("equipped_title").first()
    saved_ids = [s.resource_id for s in saved]
    collection_resource_ids = list({e.resource_id for e in collection_entries})
    dashboard = {
        "streak": _streak(account),
        "collections": [{
            "id": c.collection_id, "title": c.collection_name,
            "description": c.collection_description or "",
            "count": c.resource_count,
            "visibility": c.collection_visibility,
            "resources": resources_by_collection[c.collection_id],
        } for c in owned_collections],
        "saved": [_resource_data(s.resource) for s in saved],
        "collectionRecommendations": _recommendations(account, collection_resource_ids),
        "savedRecommendations": _recommendations(account, saved_ids),
        "viewed": visited,
        "progress": [{
            **_resource_data(p.resource),
            "reward": p.resource.completion_xp,
            "percent": p.percent_complete,
            "status": p.progress_status,
            "lastOpened": _dt(latest_visits.get(p.resource_id)),
        } for p in progress],
        "pathways": pathways,
    }
    return render(request, "dashboard.html", {
        "dashboard": dashboard,
        "profile_name": f"{account.acc_fname} {account.acc_lname}".strip(),
        "total_xp": gamification.total_xp if gamification else 0,
        "equipped_title": gamification.equipped_title.title_name if gamification and gamification.equipped_title else "",
    })


def _error(message, status=400):
    return JsonResponse({"error": message}, status=status)


@login_required
@require_POST
def dashboard_student_api(request):
    account = _account(request)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            return _error("Expected a JSON object.")
    except (ValueError, UnicodeDecodeError):
        return _error("Invalid JSON.")
    action = payload.get("action")

    if action == "create_collection":
        title = str(payload.get("title", "")).strip()
        description = str(payload.get("description", "")).strip()
        visibility = payload.get("visibility", "private")
        if not (1 <= len(title) <= 100) or len(description) > 400:
            return _error("Invalid collection name or description.")
        if visibility not in ("private", "unlisted", "public"):
            return _error("Invalid visibility.")
        # DB uses CHAR(8) IDs rather than autogenerated integers.
        for _ in range(5):
            try:
                with transaction.atomic():
                    collection = CuratedCollection.objects.create(
                        collection_id=f"{secrets.randbelow(100000000):08d}",
                        curator=account,
                        collection_name=title, 
                        collection_description=description,
                        collection_visibility=visibility, 
                        collection_type="general",
                        collection_add_date=timezone.now(), 
                        is_active="Y",
                    )
                return JsonResponse({"id": collection.collection_id})
            except IntegrityError:
                pass
        return _error("Could not allocate a collection ID.", 500)

    if action == "toggle_save":
        resource = get_object_or_404(CareerResource, resource_id=payload.get("resource_id"), is_active="Y")
        # Atomic with a unique (acc_id, resource_id) constraint recommended in MySQL.
        with transaction.atomic():
            existing = SavedResource.objects.filter(account=account, resource=resource)
            if existing.exists():
                existing.delete()
                saved = False
            else:
                SavedResource.objects.create(account=account, resource=resource)
                saved = True
        return JsonResponse({"saved": saved})

    if action == "visit":
        resource = get_object_or_404(CareerResource, resource_id=payload.get("resource_id"), is_active="Y")
        ResourceVisit.objects.create(account=account, resource=resource)
        UserResourceProgress.objects.get_or_create(account=account, resource=resource)
        LearningDay.objects.get_or_create(account=account, activity_date=timezone.localdate())
        return JsonResponse({"ok": True})

    if action == "increment_progress":
        resource = get_object_or_404(CareerResource, resource_id=payload.get("resource_id"), is_active="Y")
        with transaction.atomic():
            p, _ = UserResourceProgress.objects.select_for_update().get_or_create(
                account=account, resource=resource,
                defaults={"percent_complete": 0, "progress_status": "not_started"},
            )
            if p.percent_complete >= 100:
                return JsonResponse({"percent": 100, "awarded_xp": 0})
            p.percent_complete = min(p.percent_complete + 25, 100)
            if not p.started_at:
                p.started_at = timezone.now()
            p.progress_status = "completed" if p.percent_complete == 100 else "in_progress"
            if p.percent_complete == 100:
                p.completed_at = timezone.now()
            p.save(update_fields=["percent_complete", "progress_status", "started_at", "completed_at"])

            # Keep learning-day streak based on actual recorded activity.
            LearningDay.objects.get_or_create(account=account, activity_date=timezone.localdate())
            awarded_xp = 0
            if p.percent_complete == 100 and resource.completion_xp:
                xp, created = XPTransaction.objects.get_or_create(
                    event_key=f"resource_complete:{account.acc_id}:{resource.resource_id}",
                    defaults={
                        "account": account, "resource": resource,
                        "xp_amount": resource.completion_xp,
                        "base_xp": resource.completion_xp,
                        "multiplier": 1,
                        "xp_reason": "resource_completion",
                    },
                )
                if created:
                    UserGamification.objects.get_or_create(account=account)
                    UserGamification.objects.filter(account=account).update(total_xp=F("total_xp") + xp.xp_amount)
                    awarded_xp = xp.xp_amount
        return JsonResponse({"percent": p.percent_complete, "awarded_xp": awarded_xp})

    return _error("Unknown action.")
