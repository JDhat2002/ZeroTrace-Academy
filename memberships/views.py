from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from accounts.access import is_platform_admin
from accounts.models import User
from memberships.billing import BillingError, audit, process_webhook, record_collected_training
from memberships.catalogue import SEED_VERSION, plans_by_category, sync_commercial_plans
from memberships.forms import OperatingCostForm, PlanPriceForm, RevenueTargetForm, TrainingReceiptForm
from memberships.models import MembershipPlan, RevenueTarget
from memberships.money import format_inr
from memberships.revenue import revenue_report
from workspace.guards import member_required


@require_http_methods(["GET"])
def pricing_page(request):
    groups = plans_by_category()
    return render(request, "marketing/pricing.html", {
        "individual_plans": groups["individual"],
        "team_plans": groups["team"],
        "campus_plans": groups["campus"],
    })


@csrf_exempt
@require_POST
def payment_webhook(request):
    signature = request.headers.get("X-ZeroTrace-Signature", "")
    try:
        result = process_webhook(request.body, signature)
    except BillingError as exc:
        return JsonResponse({"detail": exc.message}, status=exc.status)
    return JsonResponse(result)


def _staff(request):
    if not is_platform_admin(request.user):
        raise Http404()


@member_required
@require_http_methods(["GET", "POST"])
def pricing_admin(request):
    _staff(request)
    notice = ""
    if request.method == "POST":
        plan = get_object_or_404(MembershipPlan, pk=request.POST.get("plan"))
        form = PlanPriceForm(request.POST, instance=plan)
        if form.is_valid():
            before = {
                "price_inr": plan.price_inr,
                "annual_price_inr": plan.annual_price_inr,
                "learner_seats": plan.learner_seats,
                "instructor_limit": plan.instructor_limit,
                "vm_concurrent": plan.vm_concurrent,
                "vm_hours": plan.vm_hours,
                "quote_only": plan.quote_only,
            }
            saved = form.save(commit=False)
            saved.seed_version = SEED_VERSION
            saved.save()
            audit(
                "plan_price_updated",
                user=request.user,
                category=saved.category,
                plan_code=saved.code,
                detail={"before": before, "after": {key: getattr(saved, key) for key in before}},
            )
            notice = f"{saved.name} saved. Existing renewal prices were not changed."
        else:
            notice = " ".join(str(item) for item in form.non_field_errors()) or "Check the prices and try again."
    groups = plans_by_category()
    return render(request, "app/pricing_admin.html", {
        "groups": (
            ("Individual — ZeroTrace Academy", groups["individual"]),
            ("Team — ZeroTrace Teams", groups["team"]),
            ("Campus — ZeroTrace Campus", groups["campus"]),
        ),
        "notice": notice,
    })


@member_required
@require_http_methods(["GET", "POST"])
def revenue_admin(request):
    _staff(request)
    notice = ""
    target = RevenueTarget.objects.filter(code="first-seven-months").first()
    if target is None:
        sync_commercial_plans()
        target = RevenueTarget.objects.filter(code="first-seven-months").first()
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "target" and target:
            form = RevenueTargetForm(request.POST, instance=target)
            if form.is_valid():
                form.save()
                audit("revenue_target_updated", user=request.user, detail={"amount_inr": target.amount_inr})
                notice = "Target saved. It is a business objective, not a forecast."
            else:
                notice = "Check the target and try again."
        elif action == "cost":
            form = OperatingCostForm(request.POST)
            if form.is_valid():
                cost = form.save(commit=False)
                cost.recorded_by = request.user
                cost.save()
                audit("operating_cost_recorded", user=request.user, detail={"amount_inr": cost.amount_inr})
                notice = "Operating cost recorded."
            else:
                notice = "Check the operating cost and try again."
        elif action == "training":
            form = TrainingReceiptForm(request.POST)
            if form.is_valid():
                payer = User.objects.filter(email=form.cleaned_data["email"].lower()).first()
                if payer is None:
                    notice = "No account uses that email."
                else:
                    try:
                        record_collected_training(
                            request.user,
                            payer=payer,
                            amount_inr=form.cleaned_data["amount_inr"],
                            kind=form.cleaned_data["kind"],
                            tax_inr=form.cleaned_data["tax_inr"],
                            fee_inr=form.cleaned_data["fee_inr"],
                            note=form.cleaned_data["note"],
                        )
                        notice = "Collected workshop or training payment recorded."
                    except BillingError as exc:
                        notice = exc.message
            else:
                notice = "Check the receipt and try again."
    report = revenue_report()
    target = report["target"]
    collected = report["lines"]["all"]["collected"]
    goal = target.amount_inr if target else 0
    progress = 0
    if goal:
        progress = min(100, int(collected * 100 / goal))
    return render(request, "app/revenue.html", {
        "report": report,
        "notice": notice,
        "progress": progress,
        "goal_label": format_inr(goal) if target else "",
        "target_form": RevenueTargetForm(instance=target) if target else None,
        "cost_form": OperatingCostForm(),
        "training_form": TrainingReceiptForm(),
    })
