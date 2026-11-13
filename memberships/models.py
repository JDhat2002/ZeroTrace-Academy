from django.conf import settings
from django.db import models


class MembershipPlan(models.Model):
    class Category(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        TEAM = "team", "Team"
        CAMPUS = "campus", "Campus"

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    category = models.CharField(max_length=16, choices=Category.choices, default=Category.INDIVIDUAL)
    price_inr = models.PositiveIntegerField(help_text="Monthly price in rupees. Unused when the plan is quote only.")
    annual_price_inr = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Annual price in rupees. Leave empty for a quotation. Never derived from the monthly price.",
    )
    currency = models.CharField(max_length=3, default="INR")
    interval = models.CharField(max_length=16, default="month")
    summary = models.TextField(blank=True)
    features = models.JSONField(default=list, blank=True)
    entitlements = models.JSONField(default=dict, blank=True)
    rank = models.PositiveSmallIntegerField(default=0)
    lab_minutes = models.PositiveIntegerField(default=0)
    range_minutes = models.PositiveIntegerField(default=0)
    vm_concurrent = models.PositiveSmallIntegerField(default=0)
    vm_hours = models.PositiveIntegerField(default=0)
    storage_mb = models.PositiveIntegerField(default=0)
    learner_seats = models.PositiveIntegerField(null=True, blank=True)
    instructor_limit = models.PositiveIntegerField(default=0)
    ctf_access = models.BooleanField(default=False)
    quote_only = models.BooleanField(default=False)
    checkout_enabled = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    seed_version = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["category", "sort_order", "rank"]

    def __str__(self):
        return f"{self.get_category_display()}: {self.name}"

    def seat_label(self):
        if self.quote_only:
            minimum = self.learner_seats or 0
            if minimum:
                return f"{minimum}+ learner seats"
            return "Custom learner seats"
        if self.category == self.Category.INDIVIDUAL:
            return "1 learner"
        return f"{self.learner_seats or 0} learner seats"

    def has_entitlement(self, key):
        return bool(self.entitlements.get(key))


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    class Source(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        TEAM = "team", "Team"
        CAMPUS = "campus", "Campus"

    class Interval(models.TextChoices):
        MONTH = "month", "Monthly"
        YEAR = "year", "Annual"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.INDIVIDUAL)
    billing_interval = models.CharField(max_length=16, choices=Interval.choices, default=Interval.MONTH)
    contracted_price_inr = models.PositiveIntegerField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    renews_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["source", "status"]),
        ]


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"

    class Category(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        TEAM = "team", "Team"
        CAMPUS = "campus", "Campus"

    class Kind(models.TextChoices):
        SUBSCRIPTION = "subscription", "Subscription"
        WORKSHOP = "workshop", "Workshop"
        TRAINING = "training", "Training"

    class Interval(models.TextChoices):
        MONTH = "month", "Monthly"
        YEAR = "year", "Annual"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    plan = models.ForeignKey(MembershipPlan, null=True, blank=True, on_delete=models.PROTECT)
    team = models.ForeignKey("teams.Team", null=True, blank=True, on_delete=models.PROTECT, related_name="payments")
    institution = models.ForeignKey(
        "campus.Institution",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    category = models.CharField(max_length=16, choices=Category.choices, blank=True, default="")
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.SUBSCRIPTION)
    billing_interval = models.CharField(max_length=16, choices=Interval.choices, blank=True, default="")
    amount_inr = models.PositiveIntegerField()
    tax_inr = models.PositiveIntegerField(default=0)
    fee_inr = models.PositiveIntegerField(default=0)
    refund_inr = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    provider_reference = models.CharField(max_length=128, blank=True)
    idempotency_key = models.CharField(max_length=128, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "category", "kind"]),
            models.Index(fields=["confirmed_at"]),
        ]


class Invoice(models.Model):
    class Status(models.TextChoices):
        OUTSTANDING = "outstanding", "Outstanding"
        PAID = "paid", "Paid"
        VOID = "void", "Void"

    payment = models.OneToOneField(Payment, null=True, blank=True, on_delete=models.CASCADE, related_name="invoice")
    team = models.ForeignKey("teams.Team", null=True, blank=True, on_delete=models.PROTECT, related_name="invoices")
    institution = models.ForeignKey(
        "campus.Institution",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    number = models.CharField(max_length=32, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PAID)
    category = models.CharField(max_length=16, blank=True, default="")
    kind = models.CharField(max_length=16, blank=True, default="subscription")
    amount_inr = models.PositiveIntegerField(default=0)
    tax_inr = models.PositiveIntegerField(default=0)
    issued_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField(null=True, blank=True)


class UsageRecord(models.Model):
    class Metric(models.TextChoices):
        LAB = "lab_minutes", "Lab minutes"
        RANGE = "range_minutes", "Cyber Range minutes"
        VM = "vm_sessions", "VM sessions"
        VM_HOURS = "vm_hours", "VM-hours"
        STORAGE = "storage_mb", "Storage"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usage_records")
    metric = models.CharField(max_length=32, choices=Metric.choices)
    amount = models.PositiveIntegerField(default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "metric", "recorded_at"])]


class WebhookEvent(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        APPLIED = "applied", "Applied"
        REJECTED = "rejected", "Rejected"

    event_id = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RECEIVED)
    payload_sha256 = models.CharField(max_length=64, blank=True)
    detail = models.JSONField(default=dict, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)


class BillingAudit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="billing_audits",
    )
    action = models.CharField(max_length=48)
    category = models.CharField(max_length=16, blank=True)
    plan_code = models.CharField(max_length=64, blank=True)
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["action", "created_at"])]


class OperatingCost(models.Model):
    amount_inr = models.PositiveIntegerField()
    incurred_on = models.DateField()
    note = models.CharField(max_length=200)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="operating_costs",
    )
    created_at = models.DateTimeField(auto_now_add=True)


class RevenueTarget(models.Model):
    code = models.SlugField(unique=True)
    label = models.CharField(max_length=120)
    amount_inr = models.PositiveIntegerField()
    horizon_months = models.PositiveSmallIntegerField(default=7)
    starts_on = models.DateField()
    note = models.CharField(max_length=240, blank=True)

    def __str__(self):
        return self.label
