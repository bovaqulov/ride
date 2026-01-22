from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
import logging
from telebot import TeleBot
from configuration import env
from ..models import PassengerTravel, OrderType, PassengerPost, Order, Cashback, CityPrice, RouteCashback, Route

from ..tasks.travel_tasks import notify_driver_bot

logger = logging.getLogger(__name__)


bot = TeleBot(env.MAIN_BOT)


# Telegram xabar yuborish funksiyasi
def send_message_view(order_pk):
    from datetime import datetime
    import pytz
    from ..serializers.order import OrderSerializer
    from ..models import Order

    order_n = Order.objects.get(pk=order_pk)
    order_data = OrderSerializer(order_n).data
    creator = order_data.get("creator", {})
    content = order_data.get("content_object", {})
    route = Route.objects.get(pk=content.get("route"))
    # created_at ni o'qishli formatga o'tkazish
    created_at_str = content.get('created_at')
    if created_at_str:
        try:
            dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            # Mahalliy vaqt (masalan, Tashkent UTC+5)
            dt = dt.astimezone(pytz.timezone("Asia/Tashkent"))
            created_at_formatted = dt.strftime("%d-%m-%Y %H:%M")
        except Exception:
            created_at_formatted = created_at_str
    else:
        created_at_formatted = "Noma'lum"

    message =  (
        f"📌 Yangi Buyurtma\n"
        f"Buyurtma ID: {order_data.get('id')}\n"
        f"Foydalanuvchi: {creator.get('full_name', '').title()} ({creator.get('phone')})\n"
        f"Telegram ID: {creator.get('telegram_id')}\n"
        f"Holat: {order_data.get('status', '').title()}\n"
        f"Buyurtma turi: {order_data.get('order_type', '').title()}\n\n"
        f"📍 Manzil:\n"
        f"Yo'nalish: {}\n"
        f"🚌 Travel klassi: {content.get('travel_class', '').title()}\n"
        f"💰 Narxi: {content.get('price')}\n"
        f"💬 Izoh: {content.get("comment", 'izoh yuq')}\n"
        f"💰 Qancha keshbek qo'llanildi: {content.get("cashback", 0)}\n"
        f"👥 Yo‘lovchilar soni: {content.get('passenger')}\n"
        f"🧕 Ayol yo‘lovchi mavjud: {'Ha' if content.get('has_woman') else 'Yo‘q'}\n"
        f"🕒 Yaratilgan vaqti: {created_at_formatted}")


    try:
        bot.send_message(
            chat_id=int(f"-{env.GROUP_ID}"),
            text=message
        )
    except Exception as e:
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
            content_object=instance,
            object_id=instance.pk,
        )
        try:

            user = Cashback.objects.filter(telegram_id=instance.user).first()
            if instance.cashback > 0:
                user.amount -= instance.cashback
                user.save()
            else:
                user.amount += (
                        CityPrice.objects.filter(Q(route=instance.route) & Q(tariff=instance.tariff)).first() *
                        RouteCashback.objects.filter(tariff=instance.tariff).first()).order_cashback
                user.save()

        except Exception as ex:
            logger.error(ex)

        # Celery task ishga tushishi
        transaction.on_commit(lambda: notify_driver_bot.delay(order.pk))

        # Telegram xabar yuborish

        transaction.on_commit(lambda: send_message_view(order.pk))

        logger.info(f"Order {order.pk} created from {sender.__name__} {instance.pk}")
    except Exception as e:
        logger.error(f"Failed to create Order for {sender.__name__} {instance.pk}: {e}", exc_info=True)
