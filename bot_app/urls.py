# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import calculate_views
from .views.bot_client_views import BotClientViewSet
from .views.cashback_views import CashbackViewSet
from .views.city_views import CityViewSet
from .views.driver_views import DriverViewSet, DriverTransactionViewSet
from .views.order_views import OrderViewSet
from .views.passenger_post_views import PassengerPostViewSet
from .views.passenger_travel_views import PassengerTravelViewSet
from .views.passenger_views import PassengerViewSet
from .views.route_views import RouteViewSet
from .views.sms_views import api
from .views.tariff_views import TariffViewSet

router = DefaultRouter()
router.register(r'clients', BotClientViewSet, basename='client')
router.register(r'cashback',CashbackViewSet , basename='cashback')
router.register(r'tariffs', TariffViewSet, basename='tariff')
router.register(r'travels', PassengerTravelViewSet, basename='passengertravel')
router.register(r'posts', PassengerPostViewSet, basename='passengerpost')
router.register(r'routes', RouteViewSet, basename='route')
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'transactions', DriverTransactionViewSet, basename='transaction')
router.register(r'cities', CityViewSet, basename='city')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'passengers', PassengerViewSet, basename='passenger')





urlpatterns = [
    path('sms/', api.urls),
    path('calculate/', calculate_views.calculate),
    path('', include(router.urls)),
]