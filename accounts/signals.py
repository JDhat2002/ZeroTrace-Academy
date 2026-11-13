from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User


@receiver(post_save, sender=User)
def create_related_records(sender, instance, created, **kwargs):
    if not created:
        return
    from profiles.models import UserPreference, UserProfile

    UserProfile.objects.get_or_create(user=instance)
    UserPreference.objects.get_or_create(user=instance)
