from rest_framework import serializers
from ..models import City, CityPrice


class CityPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityPrice
        fields = ["economy", "comfort", "standard"]


class CitySerializer(serializers.ModelSerializer):
    subcategory_title = serializers.CharField(source='subcategory.title', read_only=True)
    subcategory_id = serializers.IntegerField(source='subcategory.id', read_only=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = [
            'id', 'title', 'price', 'translate', 'subcategory', 'latitude', 'longitude',
            'subcategory_title', 'subcategory_id', 'is_allowed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_price(self, obj):
        # Agar select_related('cityprice') ishlatilsa, .cityprice dan foydalanish mumkin
        if hasattr(obj, 'cityprice'):
            return CityPriceSerializer(obj.cityprice).data
        try:
            return CityPriceSerializer(obj.cityprice).data
        except CityPrice.DoesNotExist:
            return {}


class CityCreateSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(required=False, write_only=True)
    longitude = serializers.FloatField(required=False, write_only=True)
    price = serializers.DictField(
        required=False,
        write_only=True,
        help_text="Price object containing economy, comfort, standard fields"
    )

    class Meta:
        model = City
        fields = [
            'title', 'subcategory', 'translate', 'is_allowed',
            'latitude', 'longitude', 'price'
        ]

    def validate(self, data):
        price = data.get('price')
        if price:
            required_fields = ['economy', 'comfort', 'standard']
            for field in required_fields:
                if field not in price:
                    raise serializers.ValidationError({
                        "price": f"{field} field is required in price object"
                    })
                if not isinstance(price[field], (int, float)):
                    try:
                        price[field] = float(price[field])
                    except (ValueError, TypeError):
                        raise serializers.ValidationError({
                            "price": f"{field} must be a number"
                        })
        return data

    def create(self, validated_data):
        price_data = validated_data.pop('price', None)
        city = super().create(validated_data)

        if price_data:
            CityPrice.objects.create(
                city=city,
                economy=price_data.get('economy', 0),
                comfort=price_data.get('comfort', 0),
                standard=price_data.get('standard', 0)
            )
        return city

    def update(self, instance, validated_data):
        price_data = validated_data.pop('price', None)
        city = super().update(instance, validated_data)

        if price_data is not None:
            city_price, created = CityPrice.objects.get_or_create(city=city)
            city_price.economy = price_data.get('economy', city_price.economy)
            city_price.comfort = price_data.get('comfort', city_price.comfort)
            city_price.standard = price_data.get('standard', city_price.standard)
            city_price.save()

        return city


# ===== Response Serializers =====

class LocationCheckSerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=True, min_value=-90, max_value=90)
    longitude = serializers.FloatField(required=True, min_value=-180, max_value=180)
    max_distance_km = serializers.FloatField(default=20.0, min_value=1, max_value=200)


class LocationCheckResponseSerializer(serializers.Serializer):
    is_in_city = serializers.BooleanField()
    city = CitySerializer(required=False)  # ⚠️ This expects a City MODEL INSTANCE, NOT a dict!
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
    city = CitySerializer()  # ⚠️ Also expects City MODEL INSTANCE
    distance_km = serializers.FloatField()
    coordinates = serializers.DictField(required=False)
    match_type = serializers.CharField()