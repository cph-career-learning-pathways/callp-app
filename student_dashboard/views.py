from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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
    return render(
        request,
        "dashboard.html",
        {
            "dashboard": MOCK_DASHBOARD,
            "is_mock_data": True,
        }
    )
