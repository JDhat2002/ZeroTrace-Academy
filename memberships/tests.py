import hashlib
import hmac
import json

from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from memberships.catalogue import sync_commercial_plans
from memberships.models import Invoice, MembershipPlan, Payment, Subscription
from memberships.services import price_for_interval
from workspace.catalogue import ensure_catalogue
from workspace.tests import member


def sign(body, secret="webhook-secret"):
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@override_settings(PAYMENT_WEBHOOK_SECRET="webhook-secret")
class CommercialProductTests(TestCase):
    def setUp(self):
        self.user = member()
        self.client.force_login(self.user)
        ensure_catalogue()

    def test_prices_come_from_the_catalogue_and_annual_is_not_derived(self):
        core = MembershipPlan.objects.get(code="core")
        self.assertEqual(core.price_inr, 499)
        self.assertEqual(core.annual_price_inr, 4990)
        self.assertEqual(price_for_interval(core, "year"), 4990)
        self.assertNotEqual(price_for_interval(core, "year"), core.price_inr * 12)
        page = self.client.get("/pricing.html")
        self.assertContains(page, "ZeroTrace Teams")
        self.assertContains(page, "ZeroTrace Campus")
        self.assertContains(page, "₹499")
        self.assertContains(page, "₹4,990")
        self.assertContains(page, "₹1,49,990")
        self.assertNotContains(page, "₹5,988")
        core.annual_price_inr = 4500
        core.save(update_fields=["annual_price_inr"])
        self.assertEqual(price_for_interval(core, "year"), 4500)
        self.assertContains(self.client.get("/pricing.html"), "₹4,500")

    def test_individual_membership_hides_team_and_campus_plans(self):
        response = self.client.get("/app/membership/")
        self.assertContains(response, "Membership Centre")
        self.assertContains(response, "Explorer")
        self.assertContains(response, "₹1,299")
        self.assertNotContains(response, "Team Starter")
        self.assertNotContains(response, "Team Growth")
        self.assertNotContains(response, "University Custom")
        self.assertNotContains(response, "College and department")
        self.assertNotContains(response, "Group learning paths")
        denied = self.client.post("/app/membership/select/", {"plan": "team-starter"})
        self.assertContains(denied, "not in the individual catalogue")
        self.user.refresh_from_db()
        self.assertEqual(self.user.membership, "free")

    def test_homepage_keeps_its_hero_and_does_not_hardcode_old_prices(self):
        response = self.client.get("/")
        self.assertContains(response, "Master the art of")
        self.assertContains(response, "ZeroTrace Teams")
        self.assertContains(response, "ZeroTrace Campus")
        self.assertNotContains(response, "₹199")

    def test_dashboard_stays_the_individual_workspace(self):
        response = self.client.get("/dashboard/")
        self.assertContains(response, "Welcome back, Ada")
        self.assertNotContains(response, "Team centre")
        self.assertNotContains(response, "Campus centre")

    def test_customised_prices_are_not_overwritten(self):
        core = MembershipPlan.objects.get(code="core")
        core.price_inr = 450
        core.annual_price_inr = 4500
        core.seed_version = 0
        core.save()
        sync_commercial_plans()
        core.refresh_from_db()
        self.assertEqual(core.price_inr, 450)
        self.assertEqual(core.annual_price_inr, 4500)

    def test_legacy_seed_prices_upgrade_once(self):
        core = MembershipPlan.objects.get(code="core")
        core.price_inr = 399
        core.annual_price_inr = 0
        core.seed_version = 0
        core.save()
        sync_commercial_plans()
        core.refresh_from_db()
        self.assertEqual(core.price_inr, 499)
        self.assertEqual(core.annual_price_inr, 4990)
        self.assertEqual(core.name, "Core")

    def _post_webhook(self, payload):
        body = json.dumps(payload).encode()
        return self.client.post(
            "/api/billing/webhook/",
            data=body,
            content_type="application/json",
            HTTP_X_ZEROTRACE_SIGNATURE=sign(body),
        )

    def test_webhook_is_idempotent_and_rejects_a_discounted_renewal(self):
        payload = {
            "id": "evt-core-1",
            "type": "payment.confirmed",
            "idempotency_key": "pay-core-1",
            "category": "individual",
            "kind": "subscription",
            "plan": "core",
            "interval": "year",
            "amount": 4990,
            "currency": "INR",
            "user_id": self.user.pk,
            "email": self.user.email,
            "tax": 100,
            "fee": 50,
        }
        first = self._post_webhook(payload)
        self.assertEqual(first.status_code, 200)
        second = self._post_webhook(payload)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["status"], "duplicate")
        self.assertEqual(Payment.objects.filter(status=Payment.Status.CONFIRMED).count(), 1)
        self.user.refresh_from_db()
        self.assertEqual(self.user.membership, "core")
        subscription = Subscription.objects.get(user=self.user, plan__code="core")
        self.assertEqual(subscription.contracted_price_inr, 4990)
        MembershipPlan.objects.filter(code="core").update(annual_price_inr=4500)
        renewal = {
            **payload,
            "id": "evt-core-2",
            "idempotency_key": "pay-core-2",
            "amount": 4500,
        }
        rejected = self._post_webhook(renewal)
        self.assertEqual(rejected.status_code, 409)
        subscription.refresh_from_db()
        self.assertEqual(subscription.contracted_price_inr, 4990)
        self.assertEqual(Payment.objects.filter(status=Payment.Status.CONFIRMED).count(), 1)
        accepted = self._post_webhook({**renewal, "id": "evt-core-3", "idempotency_key": "pay-core-3", "amount": 4990})
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(Payment.objects.filter(status=Payment.Status.CONFIRMED).count(), 2)

    def test_unsigned_webhook_cannot_activate_a_plan(self):
        response = self.client.post(
            "/api/billing/webhook/",
            data=b"{}",
            content_type="application/json",
            HTTP_X_ZEROTRACE_SIGNATURE="nope",
        )
        self.assertEqual(response.status_code, 401)
        self.user.refresh_from_db()
        self.assertEqual(self.user.membership, "free")

    def test_team_and_campus_are_isolated_and_billed_apart(self):
        owner = self.user
        other = member("grace@example.com", "grace")
        team_plan = MembershipPlan.objects.get(code="team-starter")
        campus_plan = MembershipPlan.objects.get(code="campus-starter")
        from teams.models import Team

        team = Team.objects.create(name="North Lab", owner=owner, plan=team_plan, status=Team.Status.ACTIVE)
        from campus.models import Institution

        college = Institution.objects.create(name="North College", owner=owner, plan=campus_plan, status=Institution.Status.ACTIVE)
        self.assertEqual(self.client.get(f"/app/teams/{team.slug}/").status_code, 200)
        self.assertContains(self.client.get(f"/app/teams/{team.slug}/"), "Group learning paths")
        self.assertNotContains(self.client.get(f"/app/teams/{team.slug}/"), "College and department management")
        self.client.force_login(other)
        self.assertEqual(self.client.get(f"/app/teams/{team.slug}/").status_code, 404)
        self.assertEqual(self.client.get(f"/app/campus/{college.slug}/").status_code, 404)
        self.client.force_login(owner)
        campus = self.client.get(f"/app/campus/{college.slug}/")
        self.assertContains(campus, "College and department management")
        self.assertNotContains(campus, "Group learning paths")
        paid = self._post_webhook({
            "id": "evt-team-1",
            "type": "payment.confirmed",
            "idempotency_key": "pay-team-1",
            "category": "team",
            "kind": "subscription",
            "plan": "team-starter",
            "interval": "month",
            "amount": 14999,
            "currency": "INR",
            "user_id": owner.pk,
            "email": owner.email,
            "team_id": team.pk,
        })
        self.assertEqual(paid.status_code, 200, paid.content)
        billing = self.client.get("/app/billing/")
        self.assertNotContains(billing, "14999")
        self.assertEqual(Payment.objects.filter(team=team, category=Payment.Category.TEAM).count(), 1)
        self.assertFalse(Payment.objects.filter(user=owner, category=Payment.Category.INDIVIDUAL, amount_inr=14999).exists())

    def test_seat_cap_and_revenue_excludes_unpaid_and_failed(self):
        from teams.models import Team, TeamMember
        from teams.services import TeamError, allocate_member

        plan = MembershipPlan.objects.get(code="team-starter")
        plan.learner_seats = 1
        plan.save(update_fields=["learner_seats"])
        team = Team.objects.create(name="Capped", owner=self.user, plan=plan, status=Team.Status.ACTIVE)
        learner = member("lin@example.com", "lin")
        allocate_member(self.user, team, "lin", TeamMember.Role.LEARNER)
        with self.assertRaises(TeamError):
            allocate_member(self.user, team, "lin", TeamMember.Role.LEARNER)
        extra = member("ned@example.com", "ned")
        with self.assertRaises(TeamError):
            allocate_member(self.user, team, "ned", TeamMember.Role.LEARNER)
        self.assertEqual(team.members.filter(role=TeamMember.Role.LEARNER, active=True).count(), 1)
        Payment.objects.create(user=self.user, amount_inr=499, status=Payment.Status.PENDING, category=Payment.Category.INDIVIDUAL, kind=Payment.Kind.SUBSCRIPTION)
        Payment.objects.create(user=self.user, amount_inr=1299, status=Payment.Status.FAILED, category=Payment.Category.INDIVIDUAL, kind=Payment.Kind.SUBSCRIPTION)
        Invoice.objects.create(number="ZT-TEST-1", status=Invoice.Status.OUTSTANDING, amount_inr=99999, category="individual")
        Subscription.objects.create(
            user=extra,
            plan=plan,
            status=Subscription.Status.CANCELLED,
            source=Subscription.Source.TEAM,
            billing_interval="year",
            contracted_price_inr=149990,
            renews_at=timezone.now(),
        )
        owner = member("ada-admin@example.com", "adaadmin")
        owner.role = User.Role.ADMIN
        owner.save()
        self.client.force_login(owner)
        report = self.client.get("/app/admin/revenue/")
        self.assertEqual(report.status_code, 200)
        self.assertContains(report, "not a forecast")
        self.assertContains(report, "₹0 collected toward ₹12,00,000")
        self.assertContains(report, "Outstanding invoices")
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/app/admin/revenue/").status_code, 404)

    def test_administrator_can_change_a_stored_price(self):
        admin = member("price-admin@example.com", "priceadmin")
        admin.role = User.Role.ADMIN
        admin.save()
        self.client.force_login(admin)
        plan = MembershipPlan.objects.get(code="pro")
        response = self.client.post("/app/admin/pricing/", {
            "plan": plan.pk,
            "price_inr": 1300,
            "annual_price_inr": 13000,
            "currency": "INR",
            "learner_seats": 1,
            "instructor_limit": 0,
            "vm_concurrent": 1,
            "vm_hours": 60,
            "is_public": "on",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Existing renewal prices were not changed")
        plan.refresh_from_db()
        self.assertEqual(plan.price_inr, 1300)
        self.assertEqual(plan.annual_price_inr, 13000)
        self.assertEqual(price_for_interval(plan, "year"), 13000)
        self.assertContains(self.client.get("/pricing.html"), "₹13,000")
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/app/admin/pricing/").status_code, 404)
