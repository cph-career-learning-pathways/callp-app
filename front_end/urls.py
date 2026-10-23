from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("resources/", views.resource_query, name="resource_query"),
    path("resources/", views.resource_query, name="resource_query"),
]