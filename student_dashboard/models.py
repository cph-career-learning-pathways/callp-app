from django.db import models
from django.core.validators import MaxValueValidator


# Create your models here.
class SavedResource(models.Model):
    id = models.BigAutoField(primary_key=True)
    account = models.ForeignKey(
        "front_end.Account",
        on_delete=models.CASCADE,
        related_name="saved_resources"
    )
    resource = models.ForeignKey(
        "front_end.CareerResource",
        on_delete=models.CASCADE,
        related_name="saved_by"
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "saved_resource"
        constraints = [
            models.UniqueConstraint(
                fields=["account", "resource"],
                name="unique_saved_resource"
            )
        ]


class SavedCollection(models.Model):
    id = models.BigAutoField(primary_key=True)
    account = models.ForeignKey(
        "front_end.Account",
        on_delete=models.CASCADE,
        related_name="saved_collections"
    )
    collection = models.ForeignKey(
        "front_end.CuratedCollection",
        on_delete=models.CASCADE,
        related_name="saved_by"
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "saved_collection"
        constraints = [
            models.UniqueConstraint(
                fields=["account", "collection"],
                name="unique_saved_collection"
            )
        ]

class UserResourceProgress(models.Model):
    id = models.BigAutoField(primary_key=True)
    account = models.ForeignKey(
        "front_end.Account",
        on_delete=models.CASCADE,
        related_name="resource_progress"
    )
    resource = models.ForeignKey(
        "front_end.CareerResource",
        on_delete=models.CASCADE,
        related_name="user_progress"
    )

    percent_complete = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(100)]
    )

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "user_resource_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["account", "resource"],
                name="unique_user_resource_progress"
            ),
            models.CheckConstraint(
                condition=models.Q(
                    percent_complete__gte=0,
                    percent_complete__lte=100
                    ),
                name="valid_resource_progress_pct"
            )
        ]

class ResourceVisit(models.Model):
    id = models.BigAutoField(primary_key=True)
    account = models.ForeignKey(
        "front_end.Account",
        on_delete=models.CASCADE,
        related_name="resource_visits"
    )
    resource = models.ForeignKey(
        "front_end.CareerResource",
        on_delete=models.CASCADE,
        related_name="visits"
    )
    visited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "resource_visit"
        indexes = [
            models.Index(
                fields=["account", "-visited_at"],
                name="resource_visit_acc_time"
            )
        ]


class LearningPathway(models.Model):
    id = models.BigAutoField(primary_key=True)
    account = models.ForeignKey(
        "front_end.Account",
        on_delete=models.CASCADE,
        related_name="learning_pathways"
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "learning_pathway"


class PathwayItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    pathway = models.ForeignKey(
        LearningPathway,
        on_delete=models.CASCADE,
        related_name="items"
    )
    resource = models.ForeignKey(
        "front_end.CareerResource",
        on_delete=models.CASCADE,
        related_name="pathway_items"
    )
    position = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = "pathway_item"
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["pathway", "position"],
                name="unique_pathway_position"
            ),
            models.UniqueConstraint(
                fields=["pathway", "resource"],
                name="unique_pathway_resource"
            )
        ]

class LearningDay(models.Model):
    id = models.BigAutoField(primary_key=True)

    account = models.ForeignKey(
        "front_end.Account",
        on_delete=models.CASCADE,
        related_name="learning_days"
    )
    activity_date = models.DateField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "learning_day"
        constraints = [
            models.UniqueConstraint(
                fields=["account", "activity_date"],
                name="unique_account_learning_day"
            )
        ]

