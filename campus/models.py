from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Institution(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    class Deployment(models.TextChoices):
        CLOUD = "cloud", "Cloud"
        ON_PREMISES = "on_premises", "On-premises"
        HYBRID = "hybrid", "Hybrid"

    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_institutions")
    plan = models.ForeignKey(
        "memberships.MembershipPlan",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="institutions",
    )
    subscription = models.OneToOneField(
        "memberships.Subscription",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="institution_billing",
    )
    deployment = models.CharField(max_length=20, choices=Deployment.choices, default=Deployment.CLOUD)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    contracted_seats = models.PositiveIntegerField(null=True, blank=True)
    contracted_instructors = models.PositiveIntegerField(null=True, blank=True)
    contracted_vm_concurrent = models.PositiveIntegerField(null=True, blank=True)
    contracted_vm_hours = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = (slugify(self.name) or "campus")[:60]
            slug = base
            number = 2
            while Institution.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{number}"
                number += 1
            self.slug = slug
        super().save(*args, **kwargs)
        if self.owner_id:
            CampusAccount.objects.get_or_create(
                institution=self,
                user_id=self.owner_id,
                defaults={"role": CampusAccount.Role.OWNER, "active": True},
            )

    def learner_cap(self):
        if self.plan_id and self.plan.quote_only:
            return self.contracted_seats
        if self.plan_id:
            return self.plan.learner_seats
        return None

    def instructor_cap(self):
        if self.plan_id and self.plan.quote_only:
            return self.contracted_instructors
        if self.plan_id:
            return self.plan.instructor_limit
        return None

    def vm_cap(self):
        if self.plan_id and self.plan.quote_only:
            return self.contracted_vm_concurrent or 0
        if self.plan_id:
            return self.plan.vm_concurrent
        return 0

    def vm_hour_cap(self):
        if self.plan_id and self.plan.quote_only:
            return self.contracted_vm_hours or 0
        if self.plan_id:
            return self.plan.vm_hours
        return 0


class AcademicProgramme(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="programmes")
    name = models.CharField(max_length=160)
    summary = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["institution", "name"], name="unique_programme_name")]


class Department(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=120)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["institution", "name"], name="unique_department_name"),
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name


class CampusAccount(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMINISTRATOR = "administrator", "Administrator"
        INSTRUCTOR = "instructor", "Instructor"
        STUDENT = "student", "Student"

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="accounts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="campus_accounts")
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="accounts")
    role = models.CharField(max_length=20, choices=Role.choices)
    active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["institution", "user"], name="unique_campus_account"),
        ]


class Batch(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="batches")
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="batches")
    name = models.CharField(max_length=80)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["institution", "name"], name="unique_batch_name"),
        ]
        ordering = ["name"]


class Classroom(models.Model):
    class Kind(models.TextChoices):
        GENERAL = "general", "Classroom"
        SOC = "soc", "SOC classroom"
        FORENSICS = "forensics", "Digital forensics classroom"

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="classrooms")
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="classrooms")
    batch = models.ForeignKey(Batch, null=True, blank=True, on_delete=models.SET_NULL, related_name="classrooms")
    name = models.CharField(max_length=160)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.GENERAL)
    instructor = models.ForeignKey(
        CampusAccount,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="classrooms",
    )

    class Meta:
        ordering = ["name"]


class PracticalExam(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="exams")
    title = models.CharField(max_length=160)
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="campus_exams_created")
    created_at = models.DateTimeField(auto_now_add=True)


class CampusCompetition(models.Model):
    class Kind(models.TextChoices):
        CTF = "ctf", "CTF"
        TEAMS = "teams", "Team competition"

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="competitions")
    name = models.CharField(max_length=160)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.CTF)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="campus_competitions_created")
    created_at = models.DateTimeField(auto_now_add=True)


class LabControl(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="lab_controls")
    classroom = models.ForeignKey(Classroom, null=True, blank=True, on_delete=models.SET_NULL, related_name="lab_controls")
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="lab_controls")
    lab = models.ForeignKey("labs.Lab", on_delete=models.PROTECT, related_name="campus_controls")
    action = models.CharField(max_length=24)
    outcome = models.CharField(max_length=24)
    detail = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CampusSeat(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="campus_seat")
    institution = models.CharField(max_length=160)
    institution_link = models.ForeignKey(
        Institution,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="legacy_seats",
    )
    department = models.CharField(max_length=120, blank=True)
    batch = models.CharField(max_length=80, blank=True)
    instructor_label = models.CharField(max_length=120, blank=True)
    lab_minutes = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.institution
