from rest_framework import serializers
from bot_app.models import Route, CityPrice, City, RouteCashback
from bot_app.serializers.tariff_serializer import TariffSerializer


class CitySimpleSerializer(serializers.ModelSerializer):
    city_id = serializers.IntegerField(source="id", read_only=True)
    class Meta:
        model = City
        fields = ("city_id", "title", "translate")


class CityPriceOptimizedSerializer(serializers.ModelSerializer):
    tariff_info = TariffSerializer(source='tariff', read_only=True)

    class Meta:
        model = CityPrice
        fields = ("price", 'tariff_info')

    def to_representation(self, instance):
        if instance.tariff and not instance.tariff.is_active:
            return None
        return super().to_representation(instance)



class RouteSerializer(serializers.ModelSerializer):
    route_id = serializers.IntegerField(source='id',read_only=True)
    from_city = CitySimpleSerializer(read_only=True)
    to_city = CitySimpleSerializer(read_only=True)

    class Meta:
        model = Route
        fields = ("route_id", "from_city", "to_city")


class RoutePriceOptimizedSerializer(serializers.ModelSerializer):
    route_id = serializers.IntegerField(source='id',read_only=True)
    to_city = CitySimpleSerializer(read_only=True)
    prices = serializers.SerializerMethodField()
    cashback = serializers.SerializerMethodField()

    class Meta:
        model = Route
        fields = ("route_id", "cashback", "to_city", 'prices')

    def get_prices(self, obj):
        # Prefetch orqali optimallashtirilgan malumotlar
        city_prices = CityPrice.objects.filter(route=obj)
        # None qiymatlarni filtrlash
        valid_prices = [
            price for price in city_prices
            if price.tariff is not None
        ]
        return CityPriceOptimizedSerializer(valid_prices, many=True).data

    def get_cashback(self, obj):
        try:
            city_prices = RouteCashback.objects.filter(route=obj).first()
            if city_prices:
                return city_prices.order_cashback
            return 0
        except Exception as e:
            print(e)
            return 0


