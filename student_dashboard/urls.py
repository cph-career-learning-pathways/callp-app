from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard_student, name="student_dashboard"),
]