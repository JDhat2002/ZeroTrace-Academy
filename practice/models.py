from django.conf import settings
from django.db import models


class Tool(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        BETA = "beta", "Beta"
        PREVIEW = "preview", "Preview"
        COMING_SOON = "coming_soon", "Coming soon"
        RESTRICTED = "restricted", "Restricted"
        MAINTENANCE = "maintenance", "Maintenance"

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    category = models.CharField(max_length=80)
    category_key = models.SlugField(max_length=40)
    summary = models.TextField()
    capabilities = models.JSONField(default=list, blank=True)
    required_plan = models.SlugField(default="free")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMING_SOON)
    version = models.CharField(max_length=20, blank=True)
    documentation = models.TextField(blank=True)

    class Meta:
        ordering = ["category", "name"]


class SocModule(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    summary = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="preview")

    class Meta:
        ordering = ["title"]


class Investigation(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="investigations")
    title = models.CharField(max_length=160)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ForensicTrack(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    summary = models.TextField(blank=True)

    class Meta:
        ordering = ["title"]


class ForensicCase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forensic_cases")
    title = models.CharField(max_length=160)
    status = models.CharField(max_length=32, default="assigned")
    evidence_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Challenge(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    category = models.CharField(max_length=80)
    difficulty = models.CharField(max_length=32, default="foundation")
    points = models.PositiveIntegerField(default=0)
    prompt = models.TextField(blank=True)
    flag_hash = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SCHEDULED)
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)


class Submission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ctf_submissions")
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="submissions")
    correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
