# filters.py
import django_filters
from ..models import Order, TravelStatus, OrderType
from django.utils import timezone
from datetime import timedelta


class OrderFilter(django_filters.FilterSet):
    # Asosiy filterlar
    user = django_filters.NumberFilter(field_name='user', lookup_expr='exact')
    driver = django_filters.NumberFilter(field_name='driver_id', lookup_expr='exact')
    status = django_filters.ChoiceFilter(choices=TravelStatus.choices)
    order_type = django_filters.ChoiceFilter(choices=OrderType.choices)

    # Sana filterlari
    created_at = django_filters.DateTimeFromToRangeFilter()
    updated_at = django_filters.DateTimeFromToRangeFilter()

    # Maxsus sana filterlari
    created_today = django_filters.BooleanFilter(method='filter_created_today')
    created_this_week = django_filters.BooleanFilter(method='filter_created_this_week')
    created_this_month = django_filters.BooleanFilter(method='filter_created_this_month')

    # Content type filterlari
    content_type = django_filters.CharFilter(method='filter_content_type')

    # Driver mavjudligi filteri
    has_driver = django_filters.BooleanFilter(method='filter_has_driver')

    # Narx filterlari (content_object orqali)
    min_price = django_filters.NumberFilter(method='filter_min_price')
    max_price = django_filters.NumberFilter(method='filter_max_price')

    # Status guruhlari
    status_in = django_filters.BaseInFilter(field_name='status', lookup_expr='in')
    status_not_in = django_filters.BaseInFilter(field_name='status', lookup_expr='in', exclude=True)

    # User va driver birgalikda
    user_and_driver = django_filters.CharFilter(method='filter_user_and_driver')

    class Meta:
        model = Order
        fields = {
            'user': ['exact'],
            'driver': ['exact'],
            'status': ['exact', 'in'],
            'order_type': ['exact'],
            'created_at': ['gte', 'lte', 'exact'],
            'updated_at': ['gte', 'lte', 'exact'],
        }

    def filter_created_today(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            return queryset.filter(created_at__date=today)
        return queryset

    def filter_created_this_week(self, queryset, name, value):
        if value:
            week_ago = timezone.now() - timedelta(days=7)
            return queryset.filter(created_at__gte=week_ago)
        return queryset

    def filter_created_this_month(self, queryset, name, value):
        if value:
            month_ago = timezone.now() - timedelta(days=30)
            return queryset.filter(created_at__gte=month_ago)
        return queryset

    def filter_content_type(self, queryset, name, value):
        if value:
            from django.contrib.contenttypes.models import ContentType
            try:
                content_type = ContentType.objects.get(model=value.lower())
                return queryset.filter(content_type=content_type)
            except ContentType.DoesNotExist:
                return queryset.none()
        return queryset

    def filter_has_driver(self, queryset, name, value):
        if value is True:
            return queryset.filter(driver__isnull=False)
        elif value is False:
            return queryset.filter(driver__isnull=True)
        return queryset

    def filter_min_price(self, queryset, name, value):
        if value is not None:
            # PassengerTravel va PassengerPost dan narxni filter qilish
            from django.db.models import Q
            from django.contrib.contenttypes.models import ContentType

            travel_content_type = ContentType.objects.get_for_model(
                self.Meta.model.passenger_travel.field.related_model)
            post_content_type = ContentType.objects.get_for_model(self.Meta.model.passenger_post.field.related_model)

            return queryset.filter(
                Q(content_type=travel_content_type, passenger_travel__price__gte=value) |
                Q(content_type=post_content_type, passenger_post__price__gte=value)
            )
        return queryset

    def filter_max_price(self, queryset, name, value):
        if value is not None:
            from django.db.models import Q
            from django.contrib.contenttypes.models import ContentType

            travel_content_type = ContentType.objects.get_for_model(
                self.Meta.model.passenger_travel.field.related_model)
            post_content_type = ContentType.objects.get_for_model(self.Meta.model.passenger_post.field.related_model)

            return queryset.filter(
                Q(content_type=travel_content_type, passenger_travel__price__lte=value) |
                Q(content_type=post_content_type, passenger_post__price__lte=value)
            )
        return queryset

    def filter_user_and_driver(self, queryset, name, value):
        if value:
            try:
                user_id, driver_id = map(int, value.split(','))
                return queryset.filter(user=user_id, driver_id=driver_id)
            except (ValueError, TypeError):
                return queryset.none()
        return queryset


class OrderSearchFilter(django_filters.FilterSet):
    """Qidiruv uchun alohida filter"""
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Order
        fields = ['search']

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        from django.contrib.contenttypes.models import ContentType

        if value:
            # User ID bo'yicha qidirish
            if value.isdigit():
                return queryset.filter(user=value)

            # Driver nomi bo'yicha qidirish
            return queryset.filter(
                Q(driver__name__icontains=value) |
                Q(content_type__model__icontains=value)
            )
        return queryset