    total_xp = models.PositiveIntegerField(default=0)
    equipped_title = models.ForeignKey(
        "Title", on_delete=models.DO_NOTHING,
        db_column="equipped_title_id", related_name="equipped_by",
        null=True, blank=True,
    )
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = "user_gamification"


class Title(models.Model):
    title_id = models.BigAutoField(primary_key=True)
    title_name = models.CharField(max_length=100, unique=True)
    title_description = models.CharField(max_length=255, null=True, blank=True)
    unlock_type = models.CharField(max_length=20)
    min_xp = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "title"


class AccountTitle(models.Model):
    pk = models.CompositePrimaryKey("account_id", "title_id")
    account = models.ForeignKey(
        "front_end.Account", on_delete=models.DO_NOTHING,
        db_column="acc_id", related_name="unlocked_titles",
    )
    title = models.ForeignKey(
        Title, on_delete=models.DO_NOTHING,
        db_column="title_id", related_name="account_unlocks",
    )
    unlocked_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = "account_title"


class XPTransaction(models.Model):
    xp_transaction_id = models.BigAutoField(primary_key=True)
    account = models.ForeignKey(
        "front_end.Account", on_delete=models.DO_NOTHING,
        db_column="acc_id", related_name="xp_transactions",
    )
    xp_amount = models.IntegerField()
    base_xp = models.PositiveIntegerField()
    multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    xp_reason = models.CharField(max_length=50)
    resource = models.ForeignKey(
        "front_end.CareerResource", on_delete=models.DO_NOTHING,
        db_column="resource_id", related_name="xp_transactions",
        null=True, blank=True,
    )
    user_pathway = models.ForeignKey(
        UserPathway, on_delete=models.DO_NOTHING,
        db_column="user_pathway_id", related_name="xp_transactions",
        null=True, blank=True,
    )
    awarded_at = models.DateTimeField(db_default=Now())
    event_key = models.CharField(max_length=150, unique=True)
    reverses_transaction = models.OneToOneField(
        "self", on_delete=models.DO_NOTHING,
        db_column="reverses_transaction_id", related_name="reversal",
        null=True, blank=True,
    )

    class Meta:
        managed = False
        db_table = "xp_transaction"


class PathwayProgressSummary(models.Model):
    """Read-only mapping for the MySQL pathway_progress_summary view.

    The SQL output has no declared primary key. user_pathway_id is used as
    the Django identity *assuming* the view returns one row per pathway.
    Do not use this model for inserts, updates, or deletes.
    """

    user_pathway_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(
        "front_end.Account", on_delete=models.DO_NOTHING,
        db_column="acc_id", related_name="pathway_progress_summaries",
    )
    collection = models.ForeignKey(
        "front_end.CuratedCollection", on_delete=models.DO_NOTHING,
        db_column="collection_id", related_name="pathway_progress_summaries",
    )
    pathway_status = models.CharField(max_length=20, default="not_started")
    total_resources = models.BigIntegerField(default=0)
    completed_resources = models.DecimalField(
        max_digits=23, decimal_places=0, null=True, blank=True,
    )
    percent_complete = models.DecimalField(
        max_digits=29, decimal_places=2, null=True, blank=True,
    )

    class Meta:
        managed = False
        db_table = "pathway_progress_summary"

