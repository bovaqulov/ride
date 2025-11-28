# serializers.py
from rest_framework import serializers
from ..models import City
from ..services.location_service import GlobalLocationService


class CitySerializer(serializers.ModelSerializer):
    subcategory_title = serializers.CharField(source='subcategory.title', read_only=True)
    subcategory_id = serializers.IntegerField(source='subcategory.id', read_only=True)

    class Meta:
        model = City
        fields = [
            'id', 'title', 'translate', 'subcategory', 'subcategory_title', 'subcategory_id',
            'is_allowed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CityCreateSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(required=False, write_only=True)
    longitude = serializers.FloatField(required=False, write_only=True)
    skip_location_validation = serializers.BooleanField(default=False, write_only=True)

    class Meta:
        model = City
        fields = ['title', 'subcategory', 'translate', 'is_allowed', 'latitude', 'longitude', 'skip_location_validation']

    def validate(self, data):
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        skip_validation = data.get('skip_location_validation', False)

        if latitude and longitude and not skip_validation:
            # Koordinatalarni tekshirish
            if not (-90 <= latitude <= 90):
                raise serializers.ValidationError({
                    "latitude": "Latitude -90 dan 90 gacha bo'lishi kerak"
                })
            if not (-180 <= longitude <= 180):
                raise serializers.ValidationError({
                    "longitude": "Longitude -180 dan 180 gacha bo'lishi kerak"
                })

        return data


class LocationCheckSerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=True, min_value=-90, max_value=90)
    longitude = serializers.FloatField(required=True, min_value=-180, max_value=180)
    max_distance_km = serializers.FloatField(default=20.0, min_value=1, max_value=200)


class LocationCheckResponseSerializer(serializers.Serializer):
    is_in_city = serializers.BooleanField()
    city = CitySerializer(required=False)
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