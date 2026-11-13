from django import forms
from django.core.exceptions import ValidationError

from memberships.models import MembershipPlan, OperatingCost, RevenueTarget


class PlanPriceForm(forms.ModelForm):
    class Meta:
        model = MembershipPlan
        fields = [
            "price_inr",
            "annual_price_inr",
            "currency",
            "learner_seats",
            "instructor_limit",
            "vm_concurrent",
            "vm_hours",
            "checkout_enabled",
            "is_public",
            "quote_only",
        ]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("quote_only"):
            return cleaned
        monthly = cleaned.get("price_inr")
        annual = cleaned.get("annual_price_inr")
        if self.instance.code != "free":
            if not monthly:
                raise ValidationError("Set a monthly price, or mark the plan as a custom quotation.")
            if annual is None or annual <= 0:
                raise ValidationError("Set the annual price. Annual billing uses that amount and does not calculate a discount.")
        return cleaned


class OperatingCostForm(forms.ModelForm):
    class Meta:
        model = OperatingCost
        fields = ["amount_inr", "incurred_on", "note"]


class RevenueTargetForm(forms.ModelForm):
    class Meta:
        model = RevenueTarget
        fields = ["amount_inr", "starts_on", "horizon_months", "note"]


class TrainingReceiptForm(forms.Form):
    email = forms.EmailField()
    kind = forms.ChoiceField(choices=[("workshop", "Workshop"), ("training", "Training")])
    amount_inr = forms.IntegerField(min_value=1)
    tax_inr = forms.IntegerField(min_value=0, initial=0)
    fee_inr = forms.IntegerField(min_value=0, initial=0)
    note = forms.CharField(max_length=128, required=False)
