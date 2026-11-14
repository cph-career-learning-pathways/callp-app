
    
  
"""Django models for the user dashboard, mapped to the existing MySQL schema.

The front_end app owns Account, CareerResource, and CuratedCollection.
All models are unmanaged: Django must not create or alter these MySQL tables.

This module requires Django 5.2+ for CompositePrimaryKey. The
pathway_progress_summary database view is mapped as read-only by convention.
"""

from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models.functions import Now


class SavedResource(models.Model):
    saved_resource_id = models.BigAutoField(primary_key=True)
    account = models.ForeignKey(
        "front_end.Account", on_delete=models.DO_NOTHING,
        db_column="acc_id", related_name="saved_resources",
    )
    resource = models.ForeignKey(
        "front_end.CareerResource", on_delete=models.DO_NOTHING,
        db_column="resource_id", related_name="saved_by",
    )
    saved_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = "saved_resource"


class SavedCollection(models.Model):
    saved_collection_id = models.BigAutoField(primary_key=True)
    account = models.ForeignKey(
        "front_end.Account", on_delete=models.DO_NOTHING,
        db_column="acc_id", related_name="saved_collections",
    )
    collection = models.ForeignKey(
        "front_end.CuratedCollection", on_delete=models.DO_NOTHING,
        db_column="collection_id", related_name="saved_by",
    )
    saved_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = "saved_collection"


class UserResourceProgress(models.Model):
    progress_id = models.BigAutoField(primary_key=True)
    account = models.ForeignKey(
        "front_end.Account", on_delete=models.DO_NOTHING,
        db_column="acc_id", related_name="resource_progress",
    )
    resource = models.ForeignKey(
        "front_end.CareerResource", on_delete=models.DO_NOTHING,
        db_column="resource_id", related_name="user_progress",
    )
    progress_status = models.CharField(max_length=20, default="not_started")
    percent_complete = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(100)],
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    # MySQL applies ON UPDATE CURRENT_TIMESTAMP automatically.
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = "user_resource_progress"


class ResourceVisit(models.Model):
    visit_id = models.BigAutoField(primary_key=True)
    account = models.ForeignKey(
        "front_end.Account", on_delete=models.DO_NOTHING,
        db_column="acc_id", related_name="resource_visits",
    )
    resource = models.ForeignKey(
        "front_end.CareerResource", on_delete=models.DO_NOTHING,
        db_column="resource_id", related_name="visits",
    )
    visited_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = "resource_visit"


class UserPathway(models.Model):
    user_pathway_id = models.BigAutoField(primary_key=True)
    account = models.ForeignKey(
        "front_end.Account", on_delete=models.DO_NOTHING,
        db_column="acc_id", related_name="learning_pathways",
    )
    collection = models.ForeignKey(

