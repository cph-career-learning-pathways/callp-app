from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard_student, name="dashboard_student"),
]