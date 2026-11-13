from django.conf import settings
from django.db import models


class Course(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_REVIEW = "in_review", "In review"
        APPROVED = "approved", "Approved"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"
        REJECTED = "rejected", "Rejected"
        PREVIEW = "preview", "Preview"

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    department = models.CharField(max_length=80)
    department_key = models.SlugField(max_length=40)
    academy_department = models.ForeignKey(
        "AcademyDepartment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="courses",
    )
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.BEGINNER)
    summary = models.TextField()
    outcomes = models.JSONField(default=list, blank=True)
    prerequisites = models.TextField(blank=True)
    practical_requirements = models.TextField(blank=True)
    assessment_summary = models.TextField(blank=True)
    certificate_rule = models.TextField(blank=True)
    language = models.CharField(max_length=40, default="English")
    membership_code = models.SlugField(default="free")
    price_inr = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PREVIEW)
    duration_minutes = models.PositiveIntegerField(default=0)
    instructor = models.CharField(max_length=120, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="authored_courses",
    )
    certificate_eligible = models.BooleanField(default=False)
    objective = models.CharField(max_length=32, blank=True)
    thumbnail = models.FileField(upload_to="course-thumbnails/", blank=True)
    weight_lesson = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_quiz = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_lab = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_assignment = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_final = models.PositiveSmallIntegerField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=160)
    position = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["position"]
        unique_together = [("course", "position")]


class Lesson(models.Model):
    class Kind(models.TextChoices):
        READING = "reading", "Text"
        VIDEO = "video", "Video"
        INTERACTIVE = "interactive", "Interactive tutorial"
        CODE = "code", "Code exercise"
        LAB = "lab", "Practical lab"
        QUIZ = "quiz", "Quiz"
        ASSIGNMENT = "assignment", "Assignment"
        CASE = "case", "Case study"
        DOWNLOAD = "download", "Downloadable resource"
        EXTERNAL = "external", "External resource"

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=160)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.READING)
    body = models.TextField(blank=True)
    position = models.PositiveSmallIntegerField(default=1)
    duration_minutes = models.PositiveIntegerField(default=10)
    video_reference = models.CharField(max_length=240, blank=True)
    prerequisite = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="dependents")
    lab = models.ForeignKey("labs.Lab", null=True, blank=True, on_delete=models.SET_NULL, related_name="lessons")
    practical = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["module__position", "position"]
        unique_together = [("module", "position")]


class LearningPath(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    summary = models.TextField()
    skills = models.JSONField(default=list, blank=True)
    duration_label = models.CharField(max_length=40, blank=True)
    prerequisites = models.TextField(blank=True)
    required_assessments = models.TextField(blank=True)
    required_projects = models.TextField(blank=True)
    required_labs = models.TextField(blank=True)
    certificate_eligible = models.BooleanField(default=False)
    outline = models.JSONField(default=list, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="authored_paths",
    )

    class Meta:
        ordering = ["sort_order", "title"]


class PathCourse(models.Model):
    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name="steps")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="path_steps")
    position = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["position"]
        unique_together = [("path", "course")]


class Enrolment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrolments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrolments")
    saved = models.BooleanField(default=False)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("user", "course")]
        indexes = [models.Index(fields=["user", "last_accessed_at"])]


class LessonProgress(models.Model):
    enrolment = models.ForeignKey(Enrolment, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_rows")
    video_ratio = models.PositiveSmallIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("enrolment", "lesson")]


class Certificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="certificates")
    credential_id = models.CharField(max_length=32, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "course")]


class LearningGoal(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="learning_goal")
    daily_minutes = models.PositiveSmallIntegerField(default=30)
    weekly_days = models.PositiveSmallIntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True)


class AcademyDepartment(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    overview = models.TextField()
    description = models.TextField(blank=True)
    objectives = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    topics = models.JSONField(default=list, blank=True)
    curriculum = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return self.name


class CourseInstructor(models.Model):
    class Role(models.TextChoices):
        AUTHOR = "author", "Author"
        REVIEWER = "reviewer", "Reviewer"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="instructors")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_roles")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.AUTHOR)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["course", "user"], name="unique_course_instructor")]


class CourseRevision(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="revisions")
    editor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="course_revisions")
    snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class CourseReview(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_reviews")
    rating = models.PositiveSmallIntegerField()
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["course", "user"], name="unique_course_review")]


class LessonNote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_notes")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="notes")
    body = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "lesson"], name="unique_lesson_note")]


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "lesson"], name="unique_bookmark")]


class LessonComment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_comments")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class QuestionBank(models.Model):
    department = models.ForeignKey(AcademyDepartment, null=True, blank=True, on_delete=models.SET_NULL, related_name="question_banks")
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.CASCADE, related_name="question_banks")
    title = models.CharField(max_length=160)
    topic = models.CharField(max_length=120, blank=True)
    difficulty = models.CharField(max_length=20, choices=Course.Level.choices, default=Course.Level.BEGINNER)
    objective = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="question_banks")

    def __str__(self):
        return self.title


class Question(models.Model):
    class Kind(models.TextChoices):
        MCQ = "mcq", "Multiple choice"
        MULTI = "multi", "Multiple select"
        BOOL = "bool", "True or false"
        SHORT = "short", "Short answer"
        LONG = "long", "Long answer"
        BLANK = "blank", "Fill in the blank"
        CODE = "code", "Code"
        MATCH = "match", "Matching"
        SCENARIO = "scenario", "Scenario"
        PRACTICAL = "practical", "Practical task"

    bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name="questions")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    prompt = models.TextField()
    marks = models.PositiveSmallIntegerField(default=1)
    difficulty = models.CharField(max_length=20, choices=Course.Level.choices, default=Course.Level.BEGINNER)
    objective = models.CharField(max_length=200, blank=True)
    options = models.JSONField(default=list, blank=True)
    answer_key = models.CharField(max_length=400, blank=True)

    class Meta:
        ordering = ["id"]


class Assessment(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assessments")
    lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.SET_NULL, related_name="assessments")
    bank = models.ForeignKey(QuestionBank, null=True, blank=True, on_delete=models.SET_NULL, related_name="assessments")
    title = models.CharField(max_length=160)
    instructions = models.TextField(blank=True)
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    total_marks = models.PositiveIntegerField(default=0)
    pass_percent = models.PositiveSmallIntegerField(default=70)
    randomise = models.BooleanField(default=False)
    question_count = models.PositiveSmallIntegerField(default=0)
    attempt_limit = models.PositiveSmallIntegerField(default=1)
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    negative_marking = models.BooleanField(default=False)
    auto_grade = models.BooleanField(default=True)
    is_final = models.BooleanField(default=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="assessments_created")

    class Meta:
        ordering = ["title"]


class AssessmentQuestion(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="selected_questions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="assessment_links")
    position = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["position"]
        constraints = [models.UniqueConstraint(fields=["assessment", "question"], name="unique_assessment_question")]


class Attempt(models.Model):
    class Status(models.TextChoices):
        STARTED = "started", "Started"
        SUBMITTED = "submitted", "Submitted"
        GRADED = "graded", "Graded"

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assessment_attempts")
    question_ids = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.STARTED)
    score = models.PositiveIntegerField(null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="graded_attempts",
    )

    class Meta:
        ordering = ["-started_at"]


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = models.TextField(blank=True)
    awarded = models.SmallIntegerField(null=True, blank=True)
    auto = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["attempt", "question"], name="unique_attempt_answer")]


class GradeAudit(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="grade_audits")
    action = models.CharField(max_length=40)
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CourseAssignment(models.Model):
    class Kind(models.TextChoices):
        REPORT = "report", "Written report"
        RESEARCH = "research", "Research"
        PROGRAMMING = "programming", "Programming"
        CONFIG = "config", "Configuration"
        SECURITY = "security", "Security assessment report"
        FORENSICS = "forensics", "Digital forensics report"
        SOC = "soc", "SOC investigation report"
        LAB = "lab", "Practical lab submission"
        CAPSTONE = "capstone", "Capstone project"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="course_assignments")
    lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.SET_NULL, related_name="course_assignments")
    title = models.CharField(max_length=160)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.REPORT)
    instructions = models.TextField(blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    allow_late = models.BooleanField(default=False)
    allowed_extensions = models.CharField(max_length=120, default="pdf,txt,md,png,jpg,jpeg,docx")
    max_bytes = models.PositiveIntegerField(default=10 * 1024 * 1024)
    rubric = models.TextField(blank=True)
    max_marks = models.PositiveIntegerField(default=100)
    allow_resubmit = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="assignments_created")

    class Meta:
        ordering = ["due_at", "title"]


class AssignmentSubmission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        GRADED = "graded", "Graded"
        RETURNED = "returned", "Returned"

    assignment = models.ForeignKey(CourseAssignment, on_delete=models.CASCADE, related_name="submissions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignment_submissions")
    body = models.TextField(blank=True)
    stored_name = models.CharField(max_length=80, blank=True)
    original_name = models.CharField(max_length=160, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    late = models.BooleanField(default=False)
    score = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUBMITTED)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_submissions",
    )

    class Meta:
        ordering = ["-submitted_at"]


class CurriculumRelease(models.Model):
    key = models.SlugField(unique=True)
    version = models.PositiveIntegerField(default=1)


class FoundationLevel(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    summary = models.TextField()
    topics = models.JSONField(default=list, blank=True)
    exercises = models.JSONField(default=list, blank=True)
    lesson = models.OneToOneField(Lesson, null=True, blank=True, on_delete=models.SET_NULL, related_name="foundation_level")

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return self.title


class GlossaryTerm(models.Model):
    slug = models.SlugField(unique=True)
    term = models.CharField(max_length=80)
    pronunciation = models.CharField(max_length=80, blank=True)
    explanation = models.TextField()
    example = models.TextField(blank=True)

    class Meta:
        ordering = ["term"]

    def __str__(self):
        return self.term


class GlossaryBookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="glossary_bookmarks")
    term = models.ForeignKey(GlossaryTerm, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "term"], name="unique_glossary_bookmark")]


class LearnerPlacement(models.Model):
    class Familiarity(models.TextChoices):
        NONE = "none", "None"
        SOME = "some", "Some"
        COMFORTABLE = "comfortable", "Comfortable"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="placement")
    computer = models.CharField(max_length=16, choices=Familiarity.choices, default=Familiarity.NONE)
    programming = models.CharField(max_length=16, choices=Familiarity.choices, default=Familiarity.NONE)
    networking = models.CharField(max_length=16, choices=Familiarity.choices, default=Familiarity.NONE)
    diagnostic_score = models.PositiveSmallIntegerField(default=0)
    diagnostic_total = models.PositiveSmallIntegerField(default=0)
    start_level = models.PositiveSmallIntegerField(default=0)
    credited = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)


class Announcement(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="announcements")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
