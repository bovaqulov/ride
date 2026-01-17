from rest_framework import serializers

from .driver import DriverSerializer
from .order import OrderSerializer
from ..models import PassengerToDriverReview


class PassengerToDriverReviewSerializer(serializers.ModelSerializer):
    passenger_info = serializers.SerializerMethodField()
    driver_info = serializers.SerializerMethodField()
    order_info = serializers.SerializerMethodField()

    class Meta:
        model = PassengerToDriverReview
        fields = [
            'id', 'passenger_info', 'driver_info', 'order_info',
            'commit', 'rate',
        ]
        read_only_fields = ['created_at']

    def get_passenger_info(self, obj):
        return DriverSerializer(obj.driver).data


    def get_driver_info(self, obj):
        return DriverSerializer(obj.driver).data

    def get_order_info(self, obj):
        return OrderSerializer(obj.order).data

class PassengerToDriverReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerToDriverReview
        fields = ['passenger', 'driver', 'order', 'commit', 'rate']


class PassengerToDriverReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerToDriverReview
        fields = ['commit', 'rate']