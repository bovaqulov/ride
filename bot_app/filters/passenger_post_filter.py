# filters/passenger_post_filter.py
import django_filters
from ..models import PassengerPost


class PassengerPostFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    min_created = django_filters.DateTimeFilter(field_name="created_at", lookup_expr='gte')
    max_created = django_filters.DateTimeFilter(field_name="created_at", lookup_expr='lte')

    class Meta:
        model = PassengerPost
        fields = {
            'user': ['exact'],
            'from_location': ['icontains', 'exact'],
            'to_location': ['icontains', 'exact'],
            'status': ['exact'],
        }