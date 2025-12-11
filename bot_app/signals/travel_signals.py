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


# Telegram xabar yuborish funksiyasi
def send_message_view(order_pk):
    from ..serializers.order import OrderSerializer

    order_n = Order.objects.get(pk=order_pk)
    order_data = OrderSerializer(order_n).data
    creator = order_data["creator"]
    content = order_data["content_object"]

    message = (
        f"📌 Yangi Buyurtma**\n"
        f"Buyurtma ID: {order_data['id']}\n"
        f"Foydalanuvchi: {creator['full_name']} ({creator['phone']})\n"
        f"Telegram ID: {creator['telegram_id']}\n"
        f"Holat: {order_data['status']}\n"
        f"Buyurtma turi: {order_data['order_type']}\n\n"
        f"📍 Manzil:\n"
        f"Qayerdan: {content['from_location']['city']}\n"
        f"Qayerga: {content['to_location']['city']}\n\n"
        f"🚌 Travel klassi: {content['travel_class']}\n"
        f"💰 Narxi: {content['price']}\n"
        f"👥 Yo‘lovchilar soni: {content['passenger']}\n"
        f"🧕 Ayol yo‘lovchi mavjud: {'Ha' if content['has_woman'] else 'Yo‘q'}\n"
        f"🕒 Yaratilgan vaqti: {content['created_at']}"
    )
    try:
        bot.send_message(
            chat_id=int(f"-{env.GROUP_ID}"),  # Guruh ID supergroup formatida
            text=message,
            parse_mode="HTML")

    except Exception as e:
        bot.send_message(
            chat_id=int(f"-100{env.GROUP_ID}"),
            text=message,
        )
        logger.error(f"Telegram xabari yuborilmadi: {e}")



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

        # Celery task ishga tushishi
        transaction.on_commit(lambda: notify_driver_bot.delay(order.pk))

        # Telegram xabar yuborish
        transaction.on_commit(lambda: send_message_view(order.pk))

        logger.info(f"Order {order.pk} created from {sender.__name__} {instance.pk}")
    except Exception as e:
        logger.error(f"Failed to create Order for {sender.__name__} {instance.pk}: {e}", exc_info=True)
