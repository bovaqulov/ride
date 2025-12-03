from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from ..models import Order, TravelStatus
from ..tasks.travel_tasks import notify_driver_bot, notify_passenger_bot


@receiver(post_save, sender=Order)
def create_order(sender, instance: Order, created,  **kwargs):
    if created:
        notify_driver_bot.delay(instance.pk)


@receiver(pre_save, sender=Order)
def update_order(sender, instance: Order, **kwargs):
    print(instance.status)
    if instance.driver:
        if instance.status == TravelStatus.CREATED:
            instance.status = TravelStatus.ASSIGNED
        notify_passenger_bot.delay(instance.pk)

    if instance.driver and instance.status == TravelStatus.ENDED:
        notify_passenger_bot.delay(instance.pk)

    if instance.driver and instance.status == TravelStatus.STARTED:
        notify_driver_bot.delay(instance.pk)

