# serializers/passenger_post.py
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .bot_client import BotClientSerializer
from .passenger import PassengerSerializer
from ..models import PassengerPost, Order, BotClient, Route, Passenger


class PassengerPostSerializer(serializers.ModelSerializer):
    order_id = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()
    route_id = serializers.PrimaryKeyRelatedField(
        source='route',
        queryset=Route.objects.all(),
        write_only=True
    )

    class Meta:
        model = PassengerPost
        fields = [
            'id', 'creator', 'comment', 'start_time', 'order_id', 'from_location', 'to_location', "route_id",
        ]
        read_only_fields = ['id']

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
            creator = Passenger.objects.get(telegram_id=obj.user)
            return PassengerSerializer(creator).data
        except Passenger.DoesNotExist:
            return {}

class PassengerPostCreateSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField()

    class Meta:
        model = PassengerPost
        fields = ['user', 'creator', 'comment', 'start_time', 'from_location', 'to_location', "cashback", "route_id"]

    def get_creator(self, obj):
        """Get creator after object is created"""
        try:
            creator = BotClient.objects.get(telegram_id=obj.user)
            return BotClientSerializer(creator).data
        except BotClient.DoesNotExist:
            return {}


class PassengerPostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerPost
        fields = ['from_location', 'to_location', ]


class PassengerPostListSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField()

    class Meta:
        model = PassengerPost
        fields = ['id', 'user', 'creator','comment', 'start_time', 'from_location', 'to_location',]

    def get_creator(self, obj):
        """Get creator after object is created"""
        try:
            creator = Passenger.objects.get(telegram_id=obj.user)
            return PassengerSerializer(creator).data
        except Passenger.DoesNotExist:
            return {}