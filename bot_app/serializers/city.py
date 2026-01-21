# serializers.py
from rest_framework import serializers
from ..models import City


class CitySerializer(serializers.ModelSerializer):

    class Meta:
        model = City
        fields = [
            'id', 'title', 'translate', 'latitude', 'longitude',
            'is_allowed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class LocationCheckSerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=True, min_value=-90, max_value=90)
    longitude = serializers.FloatField(required=True, min_value=-180, max_value=180)
    max_distance_km = serializers.FloatField(default=20.0, min_value=1, max_value=200)


class LocationCheckResponseSerializer(serializers.Serializer):
    is_in_city = serializers.BooleanField()
    city = serializers.DictField(required=False)  # ✅ shunday qiling
    distance_km = serializers.FloatField(required=False)
    address_info = serializers.DictField()
    message = serializers.CharField()
    match_type = serializers.CharField(required=False)


class CityValidationSerializer(serializers.Serializer):
    city_name = serializers.CharField(required=True)
    latitude = serializers.FloatField(required=True, min_value=-90, max_value=90)
    longitude = serializers.FloatField(required=True, min_value=-180, max_value=180)


class CityValidationResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    distance_km = serializers.FloatField()
    max_distance_km = serializers.FloatField()
    city_coordinates = serializers.DictField()
    user_location = serializers.DictField()
    city_location = serializers.DictField()
    message = serializers.CharField()


class NearbyCitiesResponseSerializer(serializers.Serializer):
    city = CitySerializer()
    distance_km = serializers.FloatField()
    coordinates = serializers.DictField(required=False)
    match_type = serializers.CharField()
