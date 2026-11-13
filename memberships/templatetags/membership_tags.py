from django import template

from memberships.money import format_inr

register = template.Library()


@register.filter
def inr(value):
    if value is None or value == "":
        return "—"
    return format_inr(value)
