"""Django models for the existing MySQL career-resource schema.

Requires Django 5.2+ for CompositePrimaryKey.
All tables are unmanaged: Django will not create, alter, or drop them.
"""
from django.db import models


YES_NO = [('Y', 'Yes'), ('N', 'No')]


class Account(models.Model):
    acc_id = models.CharField(max_length=8, primary_key=True)
    acc_fname = models.CharField(max_length=100)
    acc_lname = models.CharField(max_length=100)
    acc_email = models.CharField(max_length=50, unique=True)
    acc_role = models.CharField(max_length=10, choices=[(x, x) for x in ('student', 'teacher', 'admin', 'alumni', 'developer', 'system')])
    acc_status = models.CharField(max_length=20, choices=[(x, x) for x in ('active', 'inactive', 'suspended', 'pending', 'locked', 'archived', 'deleted')])

    class Meta:
        managed = False
        db_table = 'account'


class Category(models.Model):
    category_id = models.CharField(max_length=8, primary_key=True)
    curator = models.ForeignKey(Account, on_delete=models.DO_NOTHING, db_column='curator_id', default='11111111', related_name='curated_categories')
    category_type = models.CharField(max_length=20, choices=[(x, x) for x in ('skill', 'degree program', 'career field')])
    category_name = models.CharField(max_length=100)
    is_active = models.CharField(max_length=1, choices=YES_NO, default='Y')

    class Meta:
        managed = False
        db_table = 'category'
        constraints = [models.UniqueConstraint(fields=['category_type', 'category_name'], name='category_type_name_unique')]


class Source(models.Model):
    source_id = models.CharField(max_length=8, primary_key=True)
    curator = models.ForeignKey(Account, on_delete=models.DO_NOTHING, db_column='curator_id', default='11111111', related_name='curated_sources')
    source_name = models.CharField(max_length=50, null=True, blank=True)
    source_domain = models.CharField(max_length=253, null=True, blank=True)
    source_trust = models.CharField(max_length=7, default='normal', choices=[(x, x) for x in ('trusted', 'normal', 'blocked')])
    source_add_date = models.DateTimeField()
    source_up_date = models.DateTimeField(null=True, blank=True)
    is_active = models.CharField(max_length=1, choices=YES_NO, default='Y')

    class Meta:
        managed = False
        db_table = 'source'


class PriceModel(models.Model):
    price_model_id = models.CharField(max_length=8, primary_key=True)
    price_model_name = models.CharField(max_length=20, unique=True)
    is_active = models.CharField(max_length=1, choices=YES_NO, default='Y')

    class Meta:
        managed = False
        db_table = 'price_model'


class Filter(models.Model):
    filter_id = models.CharField(max_length=8, primary_key=True)
    curator = models.ForeignKey(Account, on_delete=models.DO_NOTHING, db_column='curator_id', default='11111111', related_name='curated_filters')
    filter_type = models.CharField(max_length=30)
    filter_name = models.CharField(max_length=30)
    is_active = models.CharField(max_length=1, choices=YES_NO, default='Y')

    class Meta:
        managed = False
        db_table = 'filter'
        constraints = [models.UniqueConstraint(fields=['filter_type', 'filter_name'], name='filter_type_name_unique')]


class CareerResource(models.Model):
    resource_id = models.CharField(max_length=8, primary_key=True)
    curator = models.ForeignKey(Account, on_delete=models.DO_NOTHING, db_column='curator_id', default='11111111', related_name='career_resources')
    is_anonymous = models.CharField(max_length=1, choices=YES_NO, default='N')
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING, db_column='source_id', related_name='career_resources')
    resource_title = models.CharField(max_length=150)
    resource_url = models.CharField(max_length=767, unique=True)
    resource_type = models.CharField(max_length=15, choices=[(x, x) for x in ('course', 'article', 'collection')])
    resource_format = models.CharField(max_length=20, choices=[(x, x) for x in ('video', 'document', 'webpage', 'mixed')])
    resource_snippet = models.TextField(null=True, blank=True)
    resource_pub_date = models.DateTimeField(null=True, blank=True)
    resource_refresh_date = models.DateTimeField()
    resource_duration = models.PositiveBigIntegerField(null=True, blank=True)
    price_model = models.ForeignKey(PriceModel, on_delete=models.DO_NOTHING, db_column='price_model_id', related_name='career_resources')
    other_metadata = models.JSONField(null=True, blank=True)
    is_active = models.CharField(max_length=1, choices=YES_NO, default='Y')

    class Meta:
        managed = False
        db_table = 'career_resource'


class CuratedCollection(models.Model):
    collection_id = models.CharField(max_length=8, primary_key=True)
    curator = models.ForeignKey(Account, on_delete=models.DO_NOTHING, db_column='curator_id', default='11111111', related_name='curated_collections')
    collection_name = models.CharField(max_length=100)
    collection_description = models.TextField(null=True, blank=True)
    collection_add_date = models.DateTimeField()
    collection_up_date = models.DateTimeField(null=True, blank=True)
    is_active = models.CharField(max_length=1, choices=YES_NO, default='Y')

    class Meta:
        managed = False
        db_table = 'curated_collection'


class UserInterests(models.Model):
    pk = models.CompositePrimaryKey('user_id', 'category_id')
    user = models.ForeignKey(Account, on_delete=models.DO_NOTHING, db_column='user_id', related_name='user_interests')
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, db_column='category_id', related_name='user_interests')
    intr_date = models.DateTimeField()
    intr_score = models.PositiveSmallIntegerField(null=True, blank=True, validators=[])

    class Meta:
        managed = False
        db_table = 'user_interests'


class CollectionResources(models.Model):
    pk = models.CompositePrimaryKey('collection_id', 'resource_id')
    collection = models.ForeignKey(CuratedCollection, on_delete=models.DO_NOTHING, db_column='collection_id', related_name='collection_resources')
    resource = models.ForeignKey(CareerResource, on_delete=models.DO_NOTHING, db_column='resource_id', related_name='collection_resources')
    sort_order = models.PositiveSmallIntegerField()
    add_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'collection_resources'


class ResourceCategory(models.Model):
    pk = models.CompositePrimaryKey('resource_id', 'category_id')
    resource = models.ForeignKey(CareerResource, on_delete=models.DO_NOTHING, db_column='resource_id', related_name='resource_categories')
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, db_column='category_id', related_name='resource_categories')

    class Meta:
        managed = False
        db_table = 'resource_category'


class ResourceFilter(models.Model):
    pk = models.CompositePrimaryKey('resource_id', 'filter_id')
    resource = models.ForeignKey(CareerResource, on_delete=models.DO_NOTHING, db_column='resource_id', related_name='resource_filters')
    filter = models.ForeignKey(Filter, on_delete=models.DO_NOTHING, db_column='filter_id', related_name='resource_filters')

    class Meta:
        managed = False
        db_table = 'resource_filter'


class CategoryParent(models.Model):
    pk = models.CompositePrimaryKey('skill_id', 'parent_id')
    skill = models.ForeignKey(Category, on_delete=models.DO_NOTHING, db_column='skill_id', related_name='parent_links')
    parent = models.ForeignKey(Category, on_delete=models.DO_NOTHING, db_column='parent_id', related_name='skill_links')

    class Meta:
        managed = False
        db_table = 'category_parent'
