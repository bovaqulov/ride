# services/passenger_service.py - notify metodida debug qo'shamiz
import logging

from ..models import Order
from ..serializers.order import OrderSerializer
from ..services.base import BaseService

logger = logging.getLogger(__name__)

class PassengerService(BaseService):
    def notify(self, order_id):
        try:
            order = Order.objects.get(id=order_id)
            data = OrderSerializer(order).data
            return self._request(
                "POST",
                'passenger',
                driver = False,
                json=data
            )
        except Exception as e:
            print(e)



