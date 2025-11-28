# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.bot_client_views import BotClientViewSet, BotClientPublicViewSet
from .views.city_views import CityViewSet
from .views.driver_views import DriverViewSet, CarViewSet, DriverTransactionViewSet
from .views.passenger_post_views import PassengerPostViewSet
from .views.passenger_travel_views import PassengerTravelViewSet

router = DefaultRouter()
router.register(r'clients', BotClientViewSet, basename='client')
router.register(r'public/clients', BotClientPublicViewSet, basename='public-client')
router.register(r'travels', PassengerTravelViewSet, basename='passengertravel')
router.register(r'posts', PassengerPostViewSet, basename='passengerpost')

router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'cars', CarViewSet, basename='car')
router.register(r'transactions', DriverTransactionViewSet, basename='transaction')
router.register(r'cities', CityViewSet, basename='city')



urlpatterns = [
    path('', include(router.urls)),
]