# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from ...models import PassengerTravel
from ...tasks.travel_create import notify_driver_bot

@receiver(post_save, sender=PassengerTravel)
def notify_driver_on_travel_creation(sender, instance, created, **kwargs):
    if created:
        # Asinxron vazifa sifatida jo'natish
        notify_driver_bot.delay(instance.id)