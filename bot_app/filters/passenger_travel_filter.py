# filters.py
import django_filters
from ..models import PassengerTravel


class PassengerTravelFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    min_passengers = django_filters.NumberFilter(field_name="passenger", lookup_expr='gte')
    max_passengers = django_filters.NumberFilter(field_name="passenger", lookup_expr='lte')

    class Meta:
        model = PassengerTravel
        fields = {
            'user': ['exact'],
            'from_location': ['icontains'],
            'to_location': ['icontains'],
            'travel_class': ['exact'],
            'status': ['exact'],
            'has_woman': ['exact'],
        }