from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Team(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_teams")
    plan = models.ForeignKey("memberships.MembershipPlan", null=True, blank=True, on_delete=models.PROTECT, related_name="teams")
    subscription = models.OneToOneField(
        "memberships.Subscription",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="team_account",
    )
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
            base = (slugify(self.name) or "team")[:60]
            slug = base
            number = 2
            while Team.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{number}"
                number += 1
            self.slug = slug
        super().save(*args, **kwargs)
        if self.owner_id:
            TeamMember.objects.get_or_create(
                team=self,
                user_id=self.owner_id,
                defaults={"role": TeamMember.Role.OWNER, "active": True},
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


class TeamMember(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMINISTRATOR = "administrator", "Administrator"
        INSTRUCTOR = "instructor", "Instructor"
        LEARNER = "learner", "Learner"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_memberships")
    role = models.CharField(max_length=20, choices=Role.choices)
    active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["team", "user"], name="unique_team_member"),
        ]


class GroupPath(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="group_paths")
    path = models.ForeignKey("learning.LearningPath", on_delete=models.PROTECT, related_name="team_assignments")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assigned_group_paths")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["team", "path"], name="unique_team_path"),
        ]


class TeamAssignment(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=160)
    brief = models.TextField(blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="team_assignments_created")
    created_at = models.DateTimeField(auto_now_add=True)


class TeamCourse(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="assigned_courses")
    course = models.ForeignKey("learning.Course", on_delete=models.CASCADE, related_name="team_assignments")
    mandatory = models.BooleanField(default=False)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="team_courses_assigned")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["team", "course"], name="unique_team_course")]


class TeamCompetition(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="competitions")
    name = models.CharField(max_length=160)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="team_competitions_created")
    created_at = models.DateTimeField(auto_now_add=True)
