# serializers/passenger_post.py
from rest_framework import serializers
from ..models import PassengerPost, TravelStatus


class PassengerPostSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PassengerPost
        fields = [
            'id', 'user', 'from_location', 'to_location', 'price',
            'status', 'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status_display']


class PassengerPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerPost
        fields = ['user', 'from_location', 'to_location', 'price']


class PassengerPostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerPost
        fields = ['from_location', 'to_location', 'price', 'status']


class PassengerPostListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PassengerPost
        fields = [
            'id', 'user', 'from_location', 'to_location', 'price',
            'status', 'status_display', 'created_at'
        ]