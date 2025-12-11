from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
import logging
from telebot import TeleBot
from configuration import env
from ..models import PassengerTravel, OrderType, PassengerPost, Order
from ..tasks.travel_tasks import notify_driver_bot

logger = logging.getLogger(__name__)


bot = TeleBot(env.MAIN_BOT)

@receiver(post_save, sender=PassengerTravel)
@receiver(post_save, sender=PassengerPost)
def create_order(sender, instance, created, **kwargs):
    if not created:
        return

    order_type = OrderType.TRAVEL if isinstance(instance, PassengerTravel) else OrderType.DELIVERY
    content_type = ContentType.objects.get_for_model(sender)

    if Order.objects.filter(content_type=content_type, object_id=instance.pk).exists():
        logger.warning(f"Order already exists for {sender.__name__} {instance.pk}")
        return

    try:
        order = Order.objects.create(
            user=instance.user,
            order_type=order_type,
            content_object=instance
        )

        transaction.on_commit(lambda: notify_driver_bot.delay(order.pk))
        transaction.on_commit(lambda: send_message(order.pk))

        def send_message(order_pk):
            try:
                bot.send_message(
                    int(f"-{env.GROUP_ID}"),
                    f"Buyurtma ID {order.pk}"
                    f""
                )
            except Exception as e:
                bot.send_message(
                    int(f"-100{env.GROUP_ID}"),
                    f"Buyurtma ID {order.pk}"
                )
        logger.info(f"Order {order.pk} created from {sender.__name__} {instance.pk}")
    except Exception as e:
        logger.error(f"Failed to create Order for {sender.__name__} {instance.pk}: {e}", exc_info=True)
