from django.contrib import admin

from memberships.models import (
    BillingAudit,
    Invoice,
    MembershipPlan,
    OperatingCost,
    Payment,
    RevenueTarget,
    Subscription,
    WebhookEvent,
)


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "code",
        "price_inr",
        "annual_price_inr",
        "learner_seats",
        "quote_only",
        "is_public",
    )
    list_filter = ("category", "quote_only", "is_public", "checkout_enabled")
    search_fields = ("name", "code")
    readonly_fields = ("seed_version",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "source", "status", "billing_interval", "contracted_price_inr", "expires_at")
    list_filter = ("source", "status", "billing_interval")
    search_fields = ("user__email", "plan__code")
    raw_id_fields = ("user",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "category", "kind", "status", "amount_inr", "refund_inr", "confirmed_at")
    list_filter = ("status", "category", "kind", "billing_interval")
    search_fields = ("user__email", "idempotency_key", "provider_reference")
    raw_id_fields = ("user", "plan", "team", "institution")
    readonly_fields = (
        "user",
        "plan",
        "team",
        "institution",
        "category",
        "kind",
        "billing_interval",
        "amount_inr",
        "tax_inr",
        "fee_inr",
        "refund_inr",
        "currency",
        "status",
        "provider_reference",
        "idempotency_key",
        "created_at",
        "confirmed_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "status", "category", "amount_inr", "issued_at")
    list_filter = ("status", "category")
    search_fields = ("number",)


@admin.register(BillingAudit)
class BillingAuditAdmin(admin.ModelAdmin):
    list_display = ("action", "category", "plan_code", "user", "created_at")
    list_filter = ("action", "category")
    readonly_fields = ("user", "action", "category", "plan_code", "detail", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(WebhookEvent)
admin.site.register(OperatingCost)
admin.site.register(RevenueTarget)
