from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models import PassengerTravel, OrderType, PassengerPost, Order


@receiver(post_save, sender=PassengerTravel)
@receiver(post_save, sender=PassengerPost)
def create_order(sender, instance, created, **kwargs):
    if created:
        if isinstance(instance, PassengerTravel):
            order_type = OrderType.TRAVEL
        else:
            order_type = OrderType.DELIVERY

        Order.objects.create(
            user=instance.user,
            order_type=order_type,
            content_object=instance
        )

