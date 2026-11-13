import random
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from learning.models import (
    Assessment,
    AssessmentQuestion,
    Attempt,
    AttemptAnswer,
    GradeAudit,
    Question,
)
from learning.services import LearningError

OBJECTIVE = {Question.Kind.MCQ, Question.Kind.MULTI, Question.Kind.BOOL, Question.Kind.SHORT, Question.Kind.BLANK}


def _selected_questions(assessment):
    linked = list(assessment.selected_questions.select_related("question"))
    if linked:
        rows = [row.question for row in linked]
    elif assessment.bank_id:
        rows = list(assessment.bank.questions.all())
    else:
        rows = []
    if assessment.randomise:
        random.shuffle(rows)
    if assessment.question_count:
        rows = rows[: assessment.question_count]
    return rows


def start_attempt(user, assessment):
    if assessment.status != Assessment.Status.PUBLISHED:
        raise LearningError("This assessment is not published.", status=403)
    now = timezone.now()
    if assessment.opens_at and now < assessment.opens_at:
        raise LearningError("This assessment is not open yet.", status=403)
    if assessment.closes_at and now > assessment.closes_at:
        raise LearningError("This assessment has closed.", status=403)
    used = assessment.attempts.filter(user=user).exclude(status=Attempt.Status.STARTED).count()
    if assessment.attempt_limit and used >= assessment.attempt_limit:
        raise LearningError("The attempt limit for this assessment has been reached.", status=403)
    open_attempt = assessment.attempts.filter(user=user, status=Attempt.Status.STARTED).first()
    if open_attempt:
        return open_attempt
    questions = _selected_questions(assessment)
    if not questions:
        raise LearningError("This assessment has no questions.", status=409)
    return Attempt.objects.create(
        assessment=assessment,
        user=user,
        question_ids=[question.pk for question in questions],
    )


def _correct_options(question):
    return {str(index) for index, option in enumerate(question.options or []) if option.get("correct")}


def grade_attempt(attempt, responses, reviewer=None):
    questions = {row.pk: row for row in Question.objects.filter(pk__in=attempt.question_ids)}
    if attempt.assessment.time_limit_minutes:
        deadline = attempt.started_at + timedelta(minutes=attempt.assessment.time_limit_minutes)
        if timezone.now() > deadline:
            raise LearningError("The time limit for this attempt has passed.", status=403)
    score = 0
    pending = False
    with transaction.atomic():
        for question_id in attempt.question_ids:
            question = questions.get(question_id)
            if question is None:
                continue
            response = (responses.get(str(question_id)) or responses.get(question_id) or "").strip()
            awarded = None
            auto = False
            if attempt.assessment.auto_grade and question.kind in OBJECTIVE:
                auto = True
                awarded = _objective_score(question, response, attempt.assessment.negative_marking)
                score += awarded
            elif question.kind not in OBJECTIVE:
                pending = True
            AttemptAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={"response": response[:4000], "awarded": awarded, "auto": auto},
            )
        attempt.score = max(score, 0)
        attempt.submitted_at = timezone.now()
        if pending:
            attempt.status = Attempt.Status.SUBMITTED
            attempt.passed = None
        else:
            total = attempt.assessment.total_marks or sum(questions[pk].marks for pk in attempt.question_ids if pk in questions)
            percent = 0 if not total else round(score / total * 100)
            attempt.passed = percent >= attempt.assessment.pass_percent
            attempt.status = Attempt.Status.GRADED
            if reviewer is not None:
                attempt.graded_by = reviewer
        attempt.save()
        GradeAudit.objects.create(
            actor=reviewer or attempt.user,
            action="attempt_submitted",
            detail={"attempt": attempt.pk, "score": score, "passed": attempt.passed},
        )
    return attempt


def _objective_score(question, response, negative):
    if question.kind == Question.Kind.MCQ:
        correct = _correct_options(question)
        awarded = question.marks if response in correct else 0
    elif question.kind == Question.Kind.MULTI:
        correct = _correct_options(question)
        given = {part.strip() for part in response.split(",") if part.strip()}
        awarded = question.marks if given == correct else 0
    elif question.kind == Question.Kind.BOOL:
        awarded = question.marks if response.lower() == (question.answer_key or "").strip().lower() else 0
    else:
        awarded = question.marks if response.casefold() == (question.answer_key or "").strip().casefold() else 0
    if negative and awarded == 0 and response:
        return -1
    return awarded


def record_manual_mark(reviewer, answer, awarded):
    if answer.question.kind in OBJECTIVE and answer.auto:
        raise LearningError("That answer was already graded automatically.", status=409)
    if awarded < 0 or awarded > answer.question.marks:
        raise LearningError("The mark is outside the question total.", status=400)
    answer.awarded = awarded
    answer.auto = False
    answer.save(update_fields=["awarded", "auto"])
    attempt = answer.attempt
    total_awarded = sum(row.awarded or 0 for row in attempt.answers.all())
    unfinished = attempt.answers.filter(awarded__isnull=True).exists()
    attempt.score = max(total_awarded, 0)
    if not unfinished:
        total = attempt.assessment.total_marks or sum(row.question.marks for row in attempt.answers.select_related("question"))
        percent = 0 if not total else round(attempt.score / total * 100)
        attempt.passed = percent >= attempt.assessment.pass_percent
        attempt.status = Attempt.Status.GRADED
        attempt.graded_by = reviewer
    attempt.save()
    GradeAudit.objects.create(
        actor=reviewer,
        action="manual_mark",
        detail={"answer": answer.pk, "awarded": awarded, "attempt": attempt.pk},
    )
    return attempt
