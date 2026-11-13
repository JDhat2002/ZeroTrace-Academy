from django.urls import path

from memberships.views import payment_webhook

urlpatterns = [
    path("webhook/", payment_webhook, name="payment-webhook"),
]
