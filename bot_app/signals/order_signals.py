from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from ..models import Order, TravelStatus, Driver
from ..tasks.travel_tasks import notify_driver_bot, notify_passenger_bot


@receiver(pre_save, sender=Order)
def update_order(sender, instance: Order, **kwargs):

    if instance.driver:
        if instance.status == TravelStatus.CREATED:
            instance.status = TravelStatus.ASSIGNED
            try:
                driver = Driver.objects.get(pk=instance.driver.pk)
                driver.amount -= instance.content_object.price * 0.05
                driver.save()
            except Exception as e:
                pass

            notify_passenger_bot.delay(instance.pk)

    if instance.driver and instance.status == TravelStatus.ENDED:
        notify_passenger_bot.delay(instance.pk)

    if instance.driver and instance.status == TravelStatus.STARTED:
        notify_driver_bot.delay(instance.pk)