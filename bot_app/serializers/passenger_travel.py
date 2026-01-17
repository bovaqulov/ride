from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import serializers

from .bot_client import BotClientSerializer
from .city import CitySerializer
from ..models import PassengerTravel, Order, BotClient, CityPrice, City, Route, Tariff


class PassengerTravelSerializer(serializers.ModelSerializer):
    from_city = serializers.SerializerMethodField()
    to_city = serializers.SerializerMethodField()
    order_id = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()


    class Meta:
        model = PassengerTravel
        fields = [
            'id', 'user','comment', 'route_id', "tariff_id", 'start_time', 'creator', 'order_id', 'from_location', 'to_location',
            'from_city', 'to_city', 'tariff_id', 'passenger',
            'price', 'has_woman', "created_at"
        ]

        read_only_fields = ['id']

    def get_from_city(self, obj):
        """from_location dan city nomini olish"""
        if isinstance(obj.from_location, dict):
            return CitySerializer(City.objects.get(id=obj.from_location.get('city_id'))).data
        return None

    def get_to_city(self, obj):
        """to_location dan city nomini olish"""
        if isinstance(obj.to_location, dict):
            return CitySerializer(City.objects.get(id=obj.to_location.get('city_id'))).data
        return None

    def get_order_id(self, obj):
        """Get order_id after object is created"""
        try:
            order = Order.objects.filter(
                content_type=ContentType.objects.get_for_model(obj),
                object_id=obj.id
            ).first()
            return order.pk if order else None
        except Order.DoesNotExist:
            return None

    def get_creator(self, obj):
        """Get creator after object is created"""
        try:
            creator = BotClient.objects.get(telegram_id=obj.user)
            return BotClientSerializer(creator).data
        except BotClient.DoesNotExist:
            return {}

    def get_price(self, obj):
        try:
            """Get price after object is created"""
            print(obj.route_id, obj.tariff_id)
            price = CityPrice.objects.filter(Q(route=obj.route_id) & Q(tariff=obj.tariff_id)).first()
            return price.price - obj.cashback
        except Exception as e:
            print(e)
            return 0

class PassengerTravelCreateSerializer(serializers.ModelSerializer):
    route_id = serializers.PrimaryKeyRelatedField(
        source='route',
        queryset=Route.objects.all(),
        write_only=True
    )
    tariff_id = serializers.PrimaryKeyRelatedField(
        source='tariff',
        queryset=Tariff.objects.all(),
        write_only=True
    )

    class Meta:
        model = PassengerTravel
        fields = [
            'user','comment', 'route_id', 'start_time', 'comment', 'from_location', 'to_location', 'tariff_id',
            'passenger', 'cashback', 'has_woman'
        ]

    def validate_from_location(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("from_location must be a JSON object")
        return value

    def validate_to_location(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("to_location must be a JSON object")
        return value

class PassengerTravelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerTravel
        fields = [
            'rate', 'tariff_id', 'passenger', 'price', 'has_woman'
        ]
