from django.db.models import Avg, Count, Q

from learning.languages import language_names
from learning.models import AcademyDepartment, Course


def catalogue(params):
    rows = Course.objects.filter(status__in=[Course.Status.PREVIEW, Course.Status.PUBLISHED]).annotate(
        review_count=Count("reviews"),
        review_average=Avg("reviews__rating"),
        module_count=Count("modules", distinct=True),
        lesson_count=Count("modules__lessons", distinct=True),
    )
    query = (params.get("q") or "").strip()
    if query:
        rows = rows.filter(Q(title__icontains=query) | Q(summary__icontains=query) | Q(department__icontains=query))
    department = params.get("department") or ""
    if department:
        rows = rows.filter(academy_department__slug=department)
    level = params.get("level") or ""
    if level in dict(Course.Level.choices):
        rows = rows.filter(level=level)
    access = params.get("access") or ""
    if access == "free":
        rows = rows.filter(membership_code="free").filter(Q(price_inr__isnull=True) | Q(price_inr=0))
    elif access == "paid":
        rows = rows.filter(Q(price_inr__gt=0) | ~Q(membership_code="free"))
    duration = params.get("duration") or ""
    if duration == "short":
        rows = rows.filter(duration_minutes__lte=120)
    elif duration == "medium":
        rows = rows.filter(duration_minutes__gt=120, duration_minutes__lte=600)
    elif duration == "long":
        rows = rows.filter(duration_minutes__gt=600)
    instructor = (params.get("instructor") or "").strip()
    if instructor:
        rows = rows.filter(instructor__icontains=instructor)
    language = (params.get("language") or "").strip()
    if language:
        rows = rows.filter(language__iexact=language)
    if params.get("certificate") == "yes":
        rows = rows.filter(certificate_eligible=True)
    if params.get("labs") == "yes":
        rows = rows.filter(Q(modules__lessons__kind="lab") | Q(modules__lessons__lab__isnull=False)).distinct()
    sort = params.get("sort") or "title"
    if sort == "recent":
        rows = rows.order_by("-published_at", "title")
    elif sort == "rating":
        rows = rows.order_by("-review_average", "-review_count", "title")
    else:
        rows = rows.order_by("title")
    return rows


def catalogue_filters():
    languages = language_names()
    published = Course.objects.filter(status__in=[Course.Status.PREVIEW, Course.Status.PUBLISHED]).values_list("language", flat=True).distinct()
    for name in published:
        if name and name not in languages:
            languages.append(name)
    return {
        "departments": AcademyDepartment.objects.all(),
        "levels": Course.Level.choices,
        "languages": languages,
    }
