# serializers/passenger_post.py
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from ..models import PassengerPost, Order


class PassengerPostSerializer(serializers.ModelSerializer):
    order_id = serializers.SerializerMethodField()

    class Meta:
        model = PassengerPost
        fields = [
            'id', 'user', 'order_id', 'from_location', 'to_location', 'price'
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

class PassengerPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerPost
        fields = ['user', 'from_location', 'to_location', 'price']


class PassengerPostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerPost
        fields = ['from_location', 'to_location', 'price', ]


class PassengerPostListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerPost
        fields = ['id', 'user', 'from_location', 'to_location', 'price']