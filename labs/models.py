from django.conf import settings
from django.db import models


class Lab(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        PREVIEW = "preview", "Preview"
        COMING_SOON = "coming_soon", "Coming soon"
        MAINTENANCE = "maintenance", "Maintenance"

    class Difficulty(models.TextChoices):
        FOUNDATION = "foundation", "Foundation"
        PRACTISING = "practising", "Practising"
        ADVANCED = "advanced", "Advanced"

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=80)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.FOUNDATION)
    summary = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    required_plan = models.SlugField(default="free")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMING_SOON)
    course = models.ForeignKey("learning.Course", null=True, blank=True, on_delete=models.SET_NULL, related_name="labs")
    environment = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["category", "name"]


class LabSession(models.Model):
    class Status(models.TextChoices):
        REJECTED = "rejected", "Rejected"
        RUNNING = "running", "Running"
        STOPPED = "stopped", "Stopped"
        COMPLETED = "completed", "Completed"
        ERROR = "error", "Error"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lab_sessions")
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name="sessions")
    status = models.CharField(max_length=16, choices=Status.choices)
    detail = models.CharField(max_length=200, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)


class VirtualMachine(models.Model):
    class Status(models.TextChoices):
        PROVISIONING = "provisioning", "Provisioning"
        STARTING = "starting", "Starting"
        RUNNING = "running", "Running"
        STOPPING = "stopping", "Stopping"
        STOPPED = "stopped", "Stopped"
        ERROR = "error", "Error"

    session = models.ForeignKey(LabSession, on_delete=models.CASCADE, related_name="machines")
    name = models.CharField(max_length=80)
    operating_system = models.CharField(max_length=80)
    status = models.CharField(max_length=20, choices=Status.choices)
    resource_profile = models.CharField(max_length=80, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
