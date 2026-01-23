import logging

from django.db.models import Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from ..models import Order, TravelStatus, Driver, Cashback, CityPrice, RouteCashback
from ..tasks.travel_tasks import notify_driver_bot, notify_passenger_bot
logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Order)
def update_order(sender, instance: Order, **kwargs):

    if instance.driver and (instance.status == TravelStatus.CREATED or instance.status == TravelStatus.ASSIGNED):

        instance.status = TravelStatus.ASSIGNED
        try:
            driver = Driver.objects.get(pk=instance.driver.pk)
            driver.amount -= instance.content_object.price * 0.05
            driver.save()
        except Exception as e:
            print(e)

        notify_passenger_bot.delay(instance.pk)

    if instance.driver and instance.status == TravelStatus.ARRIVED:
        notify_passenger_bot.delay(instance.pk)

    if instance.driver and instance.status == TravelStatus.ENDED:
        try:
            user = Cashback.objects.filter(telegram_id=instance.user).first()
            if instance.content_object.cashback > 0:
                user.amount -= instance.content_object.cashback
                user.save()
            else:
                user.amount += (
                        CityPrice.objects.filter(Q(route=instance.content_object.route) & Q(tariff=instance.content_object.tariff)).first() *
                        RouteCashback.objects.filter(tariff=instance.content_object.tariff).first()).order_cashback
                user.save()

        except Exception as ex:
            logger.error(ex)

        notify_passenger_bot.delay(instance.pk)

    if instance.driver and instance.status == TravelStatus.STARTED:
        notify_driver_bot.delay(instance.pk)