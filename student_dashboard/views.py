from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from front_end.models import Account
from .models import SavedResource

# mock data delete when done
# student_dashboard/mock_data.py

MOCK_DASHBOARD = {
    "streak": 5,
    "saved_resource_count": 12,
    "completed_count": 8,

    "pathways": [
        {
            "id": 1,
            "title": "Data Analytics Fundamentals",
            "progress": 60,
        },
        {
            "id": 2,
            "title": "Career Readiness",
            "progress": 25,
        },
    ],

    "saved_resources": [
        {
            "id": "RES00001",
            "title": "Introduction to Python",
            "type": "course",
        },
        {
            "id": "RES00002",
            "title": "SQL Fundamentals",
            "type": "article",
        },
    ],

    "saved_collections": [
        {
            "id": "COL00001",
            "name": "Data Science Starter Pack",
        },
    ],

    "recent_visits": [
        {
            "id": "RES00001",
            "title": "Introduction to Python",
            "progress": 75,
        },
        {
            "id": "RES00002",
            "title": "SQL Fundamentals",
            "progress": 40,
        },
    ],
}

# Create your views here.

@login_required
def dashboard_student(request):
    # Find the account linked to the logged-in Django user
    account = Account.objects.get(auth_user=request.user)

    # Query the actual MySQL database
    saved_resource_count = SavedResource.objects.filter(
        account=account
    ).count()

    # Preserve all other mock dashboard values
    dashboard = MOCK_DASHBOARD.copy()

    # Replace only one mock value with real database data
    dashboard["saved_resource_count"] = saved_resource_count

    return render(
        request,
        "dashboard.html",
        {
            "dashboard": dashboard,
            "is_mock_data": True,
        }
    )