from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    phone = models.CharField(max_length=20, blank=True)
    education = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile {self.user_id}"


class UserPreference(models.Model):
    class Level(models.TextChoices):
        COMPLETE_BEGINNER = "complete-beginner", "Complete Beginner"
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        PROFESSIONAL = "professional", "Professional"

    class Objective(models.TextChoices):
        FUNDAMENTALS = "fundamentals", "Build cybersecurity fundamentals"
        SOC = "soc", "Become a SOC analyst"
        PENTEST = "pentest", "Become a penetration tester"
        FORENSICS = "forensics", "Become a digital forensic investigator"
        EMPLOYMENT = "employment", "Prepare for cybersecurity employment"
        ADVANCE = "advance", "Advance existing technical skills"

    INTEREST_CHOICES = [
        ("ethical-hacking", "Ethical Hacking"),
        ("soc", "SOC Analyst"),
        ("forensics", "Digital Forensics"),
        ("cloud", "Cloud Security"),
        ("web", "Web Security"),
        ("network", "Network Security"),
        ("malware", "Malware Research"),
        ("ai", "AI Security"),
        ("engineering", "Security Engineering"),
    ]
    INTEREST_KEYS = {key for key, _label in INTEREST_CHOICES}

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preference")
    experience_level = models.CharField(max_length=32, choices=Level.choices, blank=True)
    interests = models.JSONField(default=list, blank=True)
    objective = models.CharField(max_length=32, choices=Objective.choices, blank=True)
    daily_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences {self.user_id}"
