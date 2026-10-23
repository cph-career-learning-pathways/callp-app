from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("resources/", views.resource_query, name="resource_query"),

    # Issue 35 : lazy loading collection details
    path(
        "collections/<str:collection_id>/details/", 
        views.collection_details, 
        name="collection_details"
    ),
]