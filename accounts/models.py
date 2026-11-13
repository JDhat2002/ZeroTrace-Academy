from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from accounts.countries import COUNTRY_CODES
from accounts.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Membership(models.TextChoices):
        FREE = "free", "Free"
        CORE = "core", "Core"
        PRO = "pro", "Pro"
        ELITE = "elite", "Elite"

    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        INSTRUCTOR = "instructor", "Instructor"
        ADMIN = "admin", "Administrator"

    class Interest(models.TextChoices):
        ETHICAL_HACKING = "ethical-hacking", "Ethical Hacking"
        SOC = "soc", "SOC Operations"
        FORENSICS = "forensics", "Digital Forensics"
        CLOUD = "cloud", "Cloud Security"
        MALWARE = "malware", "Malware Analysis"
        NETWORK = "network", "Network Security"
        WEB = "web", "Web Application Security"
        ENGINEERING = "engineering", "Security Engineering"
        EXPLORE = "explore", "Beginner – Explore Everything"

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=150)
    country = models.CharField(max_length=2, blank=True, default="")
    learning_interest = models.CharField(max_length=32, choices=Interest.choices)
    membership = models.CharField(max_length=16, choices=Membership.choices, default=Membership.FREE)
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    mfa_required = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    accepted_terms_at = models.DateTimeField(null=True, blank=True)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "full_name"]

    class Meta:
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["membership", "role"]),
        ]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.email = (self.email or "").lower()
        if self.country:
            self.country = self.country.upper()
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.mfa_required = True
        super().save(*args, **kwargs)

    @property
    def email_verified(self):
        return self.email_verified_at is not None

    def clean(self):
        super().clean()
        if self.country and self.country.upper() not in COUNTRY_CODES:
            from django.core.exceptions import ValidationError

            raise ValidationError({"country": "Choose a country from the list."})
