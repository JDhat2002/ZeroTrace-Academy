from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Category(models.TextChoices):
        LEARNING = "learning", "Learning"
        LAB = "lab", "Lab updates"
        RANGE = "range", "Cyber Range"
        SUBSCRIPTION = "subscription", "Subscription"
        PAYMENT = "payment", "Payment"
        SECURITY = "security", "Security"
        ANNOUNCEMENT = "announcement", "Announcements"
        CERTIFICATE = "certificate", "Certificates"
        ASSIGNMENT = "assignment", "Assignments"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    category = models.CharField(max_length=24, choices=Category.choices)
    summary = models.CharField(max_length=200)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "read_at"])]


class ActivityEvent(models.Model):
    class Category(models.TextChoices):
        LEARNING = "learning", "Learning"
        LAB = "lab", "Labs"
        RANGE = "range", "Cyber Range"
        ASSESSMENT = "assessment", "Assessments"
        CERTIFICATE = "certificate", "Certificates"
        SUBSCRIPTION = "subscription", "Subscription"
        SECURITY = "security", "Security"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_events")
    category = models.CharField(max_length=24, choices=Category.choices)
    summary = models.CharField(max_length=200)
    minutes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "category", "created_at"])]


class SupportRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_requests")
    subject = models.CharField(max_length=120)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class PrivacyRequest(models.Model):
    class Kind(models.TextChoices):
        EXPORT = "export", "Export"
        DELETION = "deletion", "Deletion"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="privacy_requests")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    created_at = models.DateTimeField(auto_now_add=True)
