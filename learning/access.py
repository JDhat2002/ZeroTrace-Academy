from accounts.access import is_instructor, is_platform_admin
from learning.models import CourseInstructor


def can_author(user):
    return is_instructor(user) or is_platform_admin(user)


def can_publish(user):
    return is_platform_admin(user)


def can_edit_course(user, course):
    if not getattr(user, "is_authenticated", False):
        return False
    if is_platform_admin(user):
        return True
    if course.created_by_id == user.id:
        return True
    return CourseInstructor.objects.filter(course=course, user=user).exists()


def can_review_submission(user, submission):
    if is_platform_admin(user):
        return True
    return can_edit_course(user, submission.assignment.course)


def can_read_submission(user, submission):
    return submission.user_id == user.id or can_review_submission(user, submission)
