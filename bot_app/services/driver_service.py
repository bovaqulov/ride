from bot_app.models import PassengerTravel
from bot_app.services.base import BaseService
from ..serializers.passenger_travel import PassengerTravelSerializer

class DriverService(BaseService):

    def notify(self, travel: PassengerTravel):

        print(travel)

        return self._request(
            "POST",
            "travel",
            json=PassengerTravelSerializer(travel).data)




