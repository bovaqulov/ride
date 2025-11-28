# bot_app/filters/driver_filter.py
from django_filters import rest_framework as filters
from django.db.models import Q
from ..models import Driver, Car, DriverTransaction, DriverStatus


class DriverFilter(filters.FilterSet):
    # Asosiy filterlar
    status = filters.ChoiceFilter(choices=DriverStatus.choices)
    from_location = filters.CharFilter(lookup_expr='icontains')
    to_location = filters.CharFilter(lookup_expr='icontains')
    phone = filters.CharFilter(lookup_expr='icontains')

    # Range filterlar
    min_amount = filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name='amount', lookup_expr='lte')
    min_rating = filters.NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = filters.NumberFilter(field_name='rating', lookup_expr='lte')

    # Date filterlar
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateFilter(field_name='created_at', lookup_expr='lte')

    # Universal location filter
    location = filters.CharFilter(method='filter_by_location')

    class Meta:
        model = Driver
        fields = ['status', 'from_location', 'to_location']

    def filter_by_location(self, queryset, name, value):
        return queryset.filter(
            Q(from_location__icontains=value) |
            Q(to_location__icontains=value)
        )


class CarFilter(filters.FilterSet):
    car_number = filters.CharFilter(lookup_expr='icontains')
    car_model = filters.CharFilter(lookup_expr='icontains')
    car_color = filters.CharFilter(lookup_expr='icontains')
    driver = filters.NumberFilter(field_name='driver__id')

    class Meta:
        model = Car
        fields = ['car_number', 'car_model', 'car_color', 'driver']


class DriverTransactionFilter(filters.FilterSet):
    driver = filters.NumberFilter(field_name='driver__id')
    min_amount = filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name='amount', lookup_expr='lte')

    class Meta:
        model = DriverTransaction
        fields = ['driver', 'amount']