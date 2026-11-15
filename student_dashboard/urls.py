from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard_student, name="dashboard_student"),
    path("dashboard/api/", views.dashboard_student_api, name="dashboard_student_api"),
]