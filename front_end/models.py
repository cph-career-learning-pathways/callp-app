from django.db import models


class User(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    user_fname = models.CharField(max_length=100)
    user_lname = models.CharField(max_length=100)
    user_email = models.EmailField(max_length=254, unique=True)
    user_role = models.CharField(max_length=30)
    user_status = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.user_fname} {self.user_lname}"


class Source(models.Model):
    source_id = models.AutoField(primary_key=True)
    curator = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="sources",
    )
    source_name = models.CharField(max_length=150)
    source_domain = models.CharField(
        max_length=253,
        unique=True,
    )
    source_trust = models.CharField(max_length=30)
    source_add_date = models.DateTimeField(auto_now_add=True)
    source_up_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.source_name


class PriceModel(models.Model):
    price_model_id = models.SmallAutoField(primary_key=True)
    price_model_name = models.CharField(
        max_length=50,
        unique=True,
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.price_model_name


class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    curator = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="categories",
    )
    category_type = models.CharField(max_length=30)
    category_name = models.CharField(max_length=150)
    category_description = models.TextField(
        null=True,
        blank=True,
    )
    category_up_date = models.DateTimeField(
        null=True,
        blank=True,
    )
    category_add_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category_type", "category_name"],
                name="unique_category_type_name",
            )
        ]

    def __str__(self):
        return self.category_name


class Filter(models.Model):
    filter_id = models.AutoField(primary_key=True)
    curator = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="filters",
    )
    filter_type = models.CharField(max_length=50)
    filter_name = models.CharField(max_length=150)
    filter_add_date = models.DateTimeField(auto_now_add=True)
    filter_up_date = models.DateTimeField(
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["filter_type", "filter_name"],
                name="unique_filter_type_name",
            )
        ]

    def __str__(self):
        return self.filter_name


class Resource(models.Model):
    resource_id = models.BigAutoField(primary_key=True)

    curator = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="resources",
    )

    is_anonymous = models.BooleanField(default=False)

    source = models.ForeignKey(
        Source,
        on_delete=models.PROTECT,
        related_name="resources",
    )

    resource_title = models.CharField(max_length=150)

    resource_url = models.URLField(max_length=2048)

    resource_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    resource_snippet = models.TextField(
        null=True,
        blank=True,
    )

    resource_up_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    resource_pub_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    resource_add_date = models.DateTimeField(
        auto_now_add=True,
    )

    resource_format = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    resource_duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    price_model = models.ForeignKey(
        PriceModel,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="resources",
    )

    price_reviewed = models.BooleanField(default=False)

    price_reviewed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="price_reviews",
    )

    price_reviewed_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    other_metadata = models.JSONField(
        null=True,
        blank=True,
    )

    categories = models.ManyToManyField(
        Category,
        through="ResourceCategory",
        related_name="resources",
    )

    filters = models.ManyToManyField(
        Filter,
        through="ResourceFilter",
        related_name="resources",
    )

    collections = models.ManyToManyField(
        "CuratedCollection",
        through="CollectionResource",
        related_name="resources",
    )

    def __str__(self):
        return self.resource_title


class CuratedCollection(models.Model):
    collection_id = models.BigAutoField(primary_key=True)

    curator = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="collections",
    )

    collection_name = models.CharField(max_length=255)

    collection_description = models.TextField(
        null=True,
        blank=True,
    )

    collection_add_date = models.DateTimeField(
        auto_now_add=True,
    )

    collection_up_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.collection_name


class ResourceCategory(models.Model):
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["resource", "category"],
                name="unique_resource_category",
            )
        ]

    def __str__(self):
        return f"{self.resource} - {self.category}"


class ResourceFilter(models.Model):
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
    )

    filter = models.ForeignKey(
        Filter,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["resource", "filter"],
                name="unique_resource_filter",
            )
        ]

    def __str__(self):
        return f"{self.resource} - {self.filter}"


class CollectionResource(models.Model):
    collection = models.ForeignKey(
        CuratedCollection,
        on_delete=models.CASCADE,
    )

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
    )

    sort_order = models.PositiveIntegerField()

    add_date = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["collection", "resource"],
                name="unique_collection_resource",
            ),
            models.UniqueConstraint(
                fields=["collection", "sort_order"],
                name="unique_collection_sort_order",
            ),
        ]

    def __str__(self):
        return f"{self.collection} - {self.resource}"