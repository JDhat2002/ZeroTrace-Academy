"""Commercial catalogue. Prices live here only as the first seed.

Later edits in the administrator pricing screen set seed_version and are left alone.
Annual prices are stored. Nothing in this module derives an annual price from a monthly one.
"""

from datetime import date

from memberships.models import MembershipPlan, RevenueTarget

SEED_VERSION = 2

INDIVIDUAL_FEATURES = {
    "free": [
        "Personal Explorer membership",
        "Preview catalogue and onboarding",
        "Personal learning record",
    ],
    "core": [
        "Personal Core membership",
        "Personal learning record",
        "Personal lab allowance",
        "Personal CTF access",
        "Personal billing",
    ],
    "pro": [
        "Personal Pro membership",
        "Personal learning record",
        "Personal lab allowance",
        "Personal CTF access",
        "Tool library when an engine is connected",
        "Personal billing",
    ],
    "elite": [
        "Personal Elite membership",
        "Personal learning record",
        "Personal lab allowance",
        "Personal CTF access",
        "Personal billing",
    ],
}

TEAM_FEATURES = [
    "Team owner account",
    "Administrator and instructor roles",
    "Learner seat allocation",
    "Group learning paths",
    "Team assignments",
    "Group CTF competitions",
    "Shared lab allowance",
    "Team performance reports",
    "Usage and resource monitoring",
    "Central billing and invoices",
]

CAMPUS_FEATURES = [
    "College and department management",
    "Student and instructor accounts",
    "Batch and classroom management",
    "Institutional seat allocation",
    "Concurrent VM and VM-hour controls",
    "Instructor lab controls",
    "Assignments and practical examinations",
    "SOC and digital forensics classrooms",
    "CTF and team competitions",
    "Institutional reporting",
    "College billing and renewals",
    "Cloud, on-premises, or hybrid deployment",
]

TEAM_ENTITLEMENTS = {
    "team_roles": True,
    "seat_allocation": True,
    "group_paths": True,
    "team_assignments": True,
    "group_ctf": True,
    "shared_labs": True,
    "team_reports": True,
    "team_usage": True,
    "team_billing": True,
}

CAMPUS_ENTITLEMENTS = {
    "departments": True,
    "campus_accounts": True,
    "batches": True,
    "classrooms": True,
    "campus_seats": True,
    "vm_controls": True,
    "instructor_labs": True,
    "exams": True,
    "soc_classrooms": True,
    "forensics_classrooms": True,
    "campus_ctf": True,
    "campus_reports": True,
    "campus_billing": True,
    "deployment_choice": True,
}


def _plan(**kwargs):
    kwargs.setdefault("currency", "INR")
    kwargs.setdefault("interval", "month")
    kwargs.setdefault("checkout_enabled", False)
    kwargs.setdefault("is_public", True)
    kwargs.setdefault("quote_only", False)
    kwargs.setdefault("entitlements", {})
    kwargs.setdefault("storage_mb", 0)
    kwargs.setdefault("ctf_access", False)
    kwargs.setdefault("lab_minutes", 0)
    kwargs.setdefault("range_minutes", 0)
    kwargs.setdefault("vm_concurrent", 0)
    kwargs.setdefault("vm_hours", 0)
    kwargs.setdefault("learner_seats", None)
    kwargs.setdefault("instructor_limit", 0)
    kwargs.setdefault("annual_price_inr", None)
    return kwargs


COMMERCIAL_PLANS = [
    _plan(
        code="free",
        legacy_monthly=0,
        name="Explorer",
        category=MembershipPlan.Category.INDIVIDUAL,
        price_inr=0,
        annual_price_inr=0,
        rank=0,
        sort_order=1,
        learner_seats=1,
        storage_mb=100,
        summary="Free individual membership. No lab hours are provisioned.",
        features=INDIVIDUAL_FEATURES["free"],
        entitlements={"personal_learning": True},
    ),
    _plan(
        code="core",
        legacy_monthly=399,
        name="Core",
        category=MembershipPlan.Category.INDIVIDUAL,
        price_inr=499,
        annual_price_inr=4990,
        rank=1,
        sort_order=2,
        learner_seats=1,
        lab_minutes=300,
        range_minutes=120,
        vm_concurrent=1,
        vm_hours=20,
        storage_mb=1024,
        ctf_access=True,
        summary="Individual Core membership. Allowances are limits, not reserved machines.",
        features=INDIVIDUAL_FEATURES["core"],
        entitlements={"personal_learning": True, "personal_labs": True, "personal_ctf": True, "personal_billing": True},
    ),
    _plan(
        code="pro",
        legacy_monthly=999,
        name="Pro",
        category=MembershipPlan.Category.INDIVIDUAL,
        price_inr=1299,
        annual_price_inr=12990,
        rank=2,
        sort_order=3,
        learner_seats=1,
        lab_minutes=900,
        range_minutes=360,
        vm_concurrent=1,
        vm_hours=60,
        storage_mb=5120,
        ctf_access=True,
        summary="Individual Pro membership. Allowances are limits, not reserved machines.",
        features=INDIVIDUAL_FEATURES["pro"],
        entitlements={"personal_learning": True, "personal_labs": True, "personal_ctf": True, "personal_billing": True},
    ),
    _plan(
        code="elite",
        legacy_monthly=1999,
        name="Elite",
        category=MembershipPlan.Category.INDIVIDUAL,
        price_inr=2499,
        annual_price_inr=24990,
        rank=3,
        sort_order=4,
        learner_seats=1,
        lab_minutes=1800,
        range_minutes=720,
        vm_concurrent=2,
        vm_hours=120,
        storage_mb=10240,
        ctf_access=True,
        summary="Individual Elite membership. Allowances are limits, not reserved machines.",
        features=INDIVIDUAL_FEATURES["elite"],
        entitlements={"personal_learning": True, "personal_labs": True, "personal_ctf": True, "personal_billing": True},
    ),
    _plan(
        code="team-starter",
        name="Team Starter",
        category=MembershipPlan.Category.TEAM,
        price_inr=14999,
        annual_price_inr=149990,
        rank=1,
        sort_order=1,
        learner_seats=5,
        instructor_limit=2,
        vm_concurrent=5,
        vm_hours=150,
        ctf_access=True,
        summary="ZeroTrace Teams. Five learner seats and a shared lab allowance.",
        features=TEAM_FEATURES,
        entitlements=TEAM_ENTITLEMENTS,
    ),
    _plan(
        code="team-growth",
        name="Team Growth",
        category=MembershipPlan.Category.TEAM,
        price_inr=24999,
        annual_price_inr=249990,
        rank=2,
        sort_order=2,
        learner_seats=10,
        instructor_limit=4,
        vm_concurrent=10,
        vm_hours=400,
        ctf_access=True,
        summary="ZeroTrace Teams. Ten learner seats and a shared lab allowance.",
        features=TEAM_FEATURES,
        entitlements=TEAM_ENTITLEMENTS,
    ),
    _plan(
        code="team-professional",
        name="Team Professional",
        category=MembershipPlan.Category.TEAM,
        price_inr=49999,
        annual_price_inr=499990,
        rank=3,
        sort_order=3,
        learner_seats=25,
        instructor_limit=8,
        vm_concurrent=25,
        vm_hours=1000,
        ctf_access=True,
        summary="ZeroTrace Teams. Twenty-five learner seats and a shared lab allowance.",
        features=TEAM_FEATURES,
        entitlements=TEAM_ENTITLEMENTS,
    ),
    _plan(
        code="team-enterprise",
        name="Team Enterprise",
        category=MembershipPlan.Category.TEAM,
        price_inr=0,
        annual_price_inr=None,
        quote_only=True,
        rank=4,
        sort_order=4,
        learner_seats=50,
        instructor_limit=0,
        summary="ZeroTrace Teams quotation for 50 or more learner seats. Limits are written on the team after the quote is accepted.",
        features=TEAM_FEATURES,
        entitlements=TEAM_ENTITLEMENTS,
    ),
    _plan(
        code="campus-starter",
        name="Starter",
        category=MembershipPlan.Category.CAMPUS,
        price_inr=9999,
        annual_price_inr=99990,
        rank=1,
        sort_order=1,
        learner_seats=10,
        instructor_limit=3,
        vm_concurrent=8,
        vm_hours=200,
        ctf_access=True,
        summary="ZeroTrace Campus. Ten institutional seats. This is not a team plan.",
        features=CAMPUS_FEATURES,
        entitlements=CAMPUS_ENTITLEMENTS,
    ),
    _plan(
        code="campus-standard",
        name="Standard",
        category=MembershipPlan.Category.CAMPUS,
        price_inr=19999,
        annual_price_inr=199990,
        rank=2,
        sort_order=2,
        learner_seats=25,
        instructor_limit=6,
        vm_concurrent=16,
        vm_hours=500,
        ctf_access=True,
        summary="ZeroTrace Campus. Twenty-five institutional seats.",
        features=CAMPUS_FEATURES,
        entitlements=CAMPUS_ENTITLEMENTS,
    ),
    _plan(
        code="campus-advanced",
        name="Advanced",
        category=MembershipPlan.Category.CAMPUS,
        price_inr=34999,
        annual_price_inr=349990,
        rank=3,
        sort_order=3,
        learner_seats=50,
        instructor_limit=12,
        vm_concurrent=30,
        vm_hours=1200,
        ctf_access=True,
        summary="ZeroTrace Campus. Fifty institutional seats.",
        features=CAMPUS_FEATURES,
        entitlements=CAMPUS_ENTITLEMENTS,
    ),
    _plan(
        code="campus-professional",
        name="Professional",
        category=MembershipPlan.Category.CAMPUS,
        price_inr=59999,
        annual_price_inr=599990,
        rank=4,
        sort_order=4,
        learner_seats=100,
        instructor_limit=20,
        vm_concurrent=50,
        vm_hours=2500,
        ctf_access=True,
        summary="ZeroTrace Campus. One hundred institutional seats.",
        features=CAMPUS_FEATURES,
        entitlements=CAMPUS_ENTITLEMENTS,
    ),
    _plan(
        code="campus-enterprise",
        name="Enterprise",
        category=MembershipPlan.Category.CAMPUS,
        price_inr=99999,
        annual_price_inr=999990,
        rank=5,
        sort_order=5,
        learner_seats=200,
        instructor_limit=40,
        vm_concurrent=80,
        vm_hours=5000,
        ctf_access=True,
        summary="ZeroTrace Campus. Two hundred institutional seats.",
        features=CAMPUS_FEATURES,
        entitlements=CAMPUS_ENTITLEMENTS,
    ),
    _plan(
        code="campus-university",
        name="University Custom",
        category=MembershipPlan.Category.CAMPUS,
        price_inr=0,
        annual_price_inr=None,
        quote_only=True,
        rank=6,
        sort_order=6,
        learner_seats=200,
        instructor_limit=0,
        summary="ZeroTrace Campus quotation for more than 200 seats. Limits are written on the institution after the quote is accepted.",
        features=CAMPUS_FEATURES,
        entitlements=CAMPUS_ENTITLEMENTS,
    ),
]

COPY_FIELDS = (
    "name",
    "category",
    "price_inr",
    "annual_price_inr",
    "currency",
    "interval",
    "summary",
    "features",
    "entitlements",
    "rank",
    "lab_minutes",
    "range_minutes",
    "vm_concurrent",
    "vm_hours",
    "storage_mb",
    "learner_seats",
    "instructor_limit",
    "ctf_access",
    "quote_only",
    "checkout_enabled",
    "is_public",
    "sort_order",
)


def plans_by_category():
    sync_commercial_plans()
    rows = MembershipPlan.objects.all()
    return {
        "individual": rows.filter(category=MembershipPlan.Category.INDIVIDUAL),
        "team": rows.filter(category=MembershipPlan.Category.TEAM),
        "campus": rows.filter(category=MembershipPlan.Category.CAMPUS),
    }


def _ensure_target():
    RevenueTarget.objects.get_or_create(
        code="first-seven-months",
        defaults={
            "label": "First seven months",
            "amount_inr": 1200000,
            "horizon_months": 7,
            "starts_on": date(2026, 11, 1),
            "note": "Business target for collected revenue. Not a prediction.",
        },
    )


def sync_commercial_plans():
    existing = {row.code: row for row in MembershipPlan.objects.all()}
    needs_plans = any(
        item["code"] not in existing or existing[item["code"]].seed_version < SEED_VERSION
        for item in COMMERCIAL_PLANS
    )
    if not needs_plans:
        if not RevenueTarget.objects.filter(code="first-seven-months").exists():
            _ensure_target()
        return
    for item in COMMERCIAL_PLANS:
        payload = {key: item[key] for key in COPY_FIELDS}
        legacy = item.get("legacy_monthly")
        row = existing.get(item["code"])
        if row is None:
            MembershipPlan.objects.create(code=item["code"], seed_version=SEED_VERSION, **payload)
            continue
        if row.seed_version >= SEED_VERSION:
            continue
        custom_price = legacy is not None and row.price_inr not in {legacy, item["price_inr"]}
        if custom_price:
            row.category = item["category"]
            if not row.entitlements:
                row.entitlements = item["entitlements"]
            row.seed_version = SEED_VERSION
            row.save(update_fields=["category", "entitlements", "seed_version"])
            continue
        for key, value in payload.items():
            setattr(row, key, value)
        row.seed_version = SEED_VERSION
        row.save()
    _ensure_target()
