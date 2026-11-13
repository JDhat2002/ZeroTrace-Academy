"""Create the Foundations course once. Later requests only confirm it exists."""

from django.db import transaction
from django.utils.text import slugify

from learning.foundation_content import (
    DIAGNOSTIC,
    GLOSSARY,
    LABS,
    LEVELS,
    PATH_SLUG,
    PROGRAMME,
    SEQUENCE,
    department_curriculum,
)
from learning.models import (
    AcademyDepartment,
    Assessment,
    AssessmentQuestion,
    Course,
    CourseAssignment,
    CurriculumRelease,
    FoundationLevel,
    GlossaryTerm,
    LearningPath,
    Lesson,
    Module,
    PathCourse,
    Question,
    QuestionBank,
)

RELEASE = "foundations-v1"


def sync_foundations():
    if CurriculumRelease.objects.filter(key=RELEASE).exists():
        return
    with transaction.atomic():
        _build()
        CurriculumRelease.objects.get_or_create(key=RELEASE, defaults={"version": 1})


def _build():
    department = AcademyDepartment.objects.filter(slug="computer-science").first()
    course, _created = Course.objects.get_or_create(
        slug=PROGRAMME["slug"],
        defaults={
            "title": PROGRAMME["title"],
            "summary": PROGRAMME["summary"],
            "department": department.name if department else "Computer Science and IT Fundamentals",
            "department_key": department.slug if department else "computer-science",
            "status": Course.Status.PUBLISHED,
            "level": Course.Level.BEGINNER,
            "language": "English",
            "membership_code": "free",
            "certificate_eligible": True,
            "certificate_rule": PROGRAMME["certificate_rule"],
            "duration_minutes": 2400,
            "outcomes": [
                "Explain a computer, an operating system, a network, and a web request in ordinary language.",
                "Write a small Python program and read a log or a hash.",
                "Apply everyday account and device habits.",
                "State when security testing is allowed.",
            ],
            "prerequisites": "None. The placement check can skip early levels when you already know them.",
            "practical_requirements": "A computer you may use. Live scans, live malware, and targets outside the written lab are not part of this course.",
            "assessment_summary": "Level notes, beginner labs, a graded capstone report, and a final examination.",
            "weight_lesson": 25,
            "weight_quiz": 20,
            "weight_lab": 30,
            "weight_assignment": 15,
            "weight_final": 10,
        },
    )
    if department and course.academy_department_id is None:
        course.academy_department = department
        course.save(update_fields=["academy_department"])
    if course.enrolments.exists() and course.modules.exists():
        return
    course.modules.all().delete()
    FoundationLevel.objects.all().delete()

    for level in LEVELS:
        module = Module.objects.create(course=course, title=f"Level {level['number']}: {level['title']}", position=level["number"] + 1)
        lesson = Lesson.objects.create(
            module=module,
            title=level["title"],
            kind=Lesson.Kind.READING,
            body=_level_body(level),
            position=1,
            duration_minutes=40,
        )
        FoundationLevel.objects.create(
            number=level["number"],
            slug=level["slug"],
            title=level["title"],
            summary=level["summary"],
            topics=level["topics"],
            exercises=level["exercises"],
            lesson=lesson,
        )

    lab_module = Module.objects.create(course=course, title="Beginner practical labs", position=20)
    for index, lab in enumerate(LABS, start=1):
        Lesson.objects.create(
            module=lab_module,
            title=lab["title"],
            kind=Lesson.Kind.INTERACTIVE,
            body=lab["objective"],
            position=index,
            duration_minutes=25,
            practical={
                "objective": lab["objective"],
                "background": lab["prerequisites"],
                "instructions": " ".join(lab["steps"]),
                "expected": lab["expected"],
                "questions": " ".join(lab["questions"]),
                "completion": lab["completion"],
                "cleanup": lab["cleanup"],
            },
        )

    capstone_module = Module.objects.create(course=course, title="Capstone", position=21)
    capstone_lesson = Lesson.objects.create(
        module=capstone_module,
        title="Foundations capstone report",
        kind=Lesson.Kind.ASSIGNMENT,
        body="Explain, in your own words, how a computer starts, how a browser reaches a page, and three habits that protect an account. Use 400 to 800 words. Do not include real passwords or another person's data.",
        position=1,
        duration_minutes=90,
    )
    CourseAssignment.objects.create(
        course=course,
        lesson=capstone_lesson,
        title="Foundations capstone report",
        kind=CourseAssignment.Kind.CAPSTONE,
        instructions=capstone_lesson.body,
        rubric="Clear explanation of boot, web requests, and three protective habits. No copied exploit steps. No real secrets.",
        max_marks=100,
        allow_resubmit=True,
        allowed_extensions="pdf,txt,md,docx",
    )
    _exam(course)
    _glossary()
    _path(course)
    apply_department_curriculum()


def _level_body(level):
    parts = [level["summary"], ""]
    for topic in level["topics"]:
        parts.append(topic["title"])
        parts.append(topic["body"])
        parts.append("")
    if level["exercises"]:
        parts.append("Practical exercises")
        for item in level["exercises"]:
            parts.append(item["title"])
            parts.append(item["instruction"])
            parts.append("")
    return "\n".join(parts)


def _exam(course):
    bank, _created = QuestionBank.objects.get_or_create(
        course=course,
        title="Foundations final examination",
        defaults={"topic": "Foundations", "difficulty": Course.Level.BEGINNER},
    )
    prompts = [
        ("Which storage keeps a file after power is lost?", [("RAM", False), ("A disk or SSD", True), ("The mouse", False)]),
        ("What is the usual job of a standard user account?", [("Change the whole system every day", False), ("Daily work without full control of the computer", True), ("Replace the operating system", False)]),
        ("What does a default gateway do?", [("Stores your files", False), ("Forwards packets toward other networks", True), ("Registers a domain name", False)]),
        ("What does a 404 status mean?", [("The file was not found", True), ("The password was correct", False), ("The disk is encrypted", False)]),
        ("What is a Python list index of the first item?", [("0", True), ("1", False), ("10", False)]),
        ("What does XOR do in the Level 5 demonstration?", [("It deletes a file", False), ("It mixes bits and can be reversed with the same mix", True), ("It assigns a public IP address", False)]),
        ("Which three aims form the CIA triad?", [("Cost, income, assets", False), ("Confidentiality, integrity, availability", True), ("Click, install, administer", False)]),
        ("What makes a security test authorised?", [("The software is old", False), ("Written scope from the owner", True), ("You intend to report it later", False)]),
    ]
    questions = []
    for prompt, options in prompts:
        questions.append(Question.objects.create(
            bank=bank,
            kind=Question.Kind.MCQ,
            prompt=prompt,
            marks=1,
            difficulty=Course.Level.BEGINNER,
            options=[{"text": text, "correct": correct} for text, correct in options],
        ))
    assessment = Assessment.objects.create(
        course=course,
        bank=bank,
        title="Foundations final examination",
        instructions="Answer from the Foundations levels. This exam is one of the certificate requirements.",
        total_marks=len(questions),
        pass_percent=70,
        attempt_limit=3,
        auto_grade=True,
        is_final=True,
        status=Assessment.Status.PUBLISHED,
    )
    for position, question in enumerate(questions, start=1):
        AssessmentQuestion.objects.create(assessment=assessment, question=question, position=position)


def _glossary():
    for term, pronunciation, explanation, example in GLOSSARY:
        GlossaryTerm.objects.update_or_create(
            slug=slugify(term)[:50],
            defaults={
                "term": term,
                "pronunciation": pronunciation,
                "explanation": explanation,
                "example": example,
            },
        )


def _path(course):
    path, _created = LearningPath.objects.get_or_create(
        slug=PATH_SLUG,
        defaults={
            "title": "Cybersecurity Fundamentals",
            "summary": "The beginner sequence from digital literacy to a foundations assessment.",
            "sort_order": 1,
        },
    )
    path.summary = "ZeroTrace Foundations, from digital basics to a beginner assessment. Early levels can be skipped only after placement."
    path.duration_label = "8–12 weeks"
    path.prerequisites = "None."
    path.required_assessments = "Foundations final examination."
    path.required_projects = "Foundations capstone report."
    path.required_labs = "Beginner practical labs in the Foundations course."
    path.outline = SEQUENCE
    path.certificate_eligible = False
    path.save()
    PathCourse.objects.get_or_create(path=path, course=course, defaults={"position": 1})


def apply_department_curriculum():
    for row in AcademyDepartment.objects.all():
        row.curriculum = department_curriculum(row.slug, row.name, row.overview, row.topics)
        row.save(update_fields=["curriculum"])
