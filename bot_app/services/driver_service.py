
from ..models import Order
from ..serializers.order import DriverOrderSerializer
from ..services.base import BaseService


class DriverService(BaseService):

    def notify(self, order_id: int):
        order = Order.objects.get(id=order_id)

        return self._request(
                "POST",
                "driver",
                json=DriverOrderSerializer(order).data)




