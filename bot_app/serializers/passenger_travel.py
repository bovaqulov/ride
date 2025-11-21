# serializers.py
from rest_framework import serializers
from ..models import PassengerTravel, TravelClass, TravelStatus


class PassengerTravelSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField()
    from_location = serializers.CharField(max_length=200)
    to_location = serializers.CharField(max_length=200)
    travel_class = serializers.ChoiceField(choices=TravelClass.choices)
    passenger = serializers.IntegerField(min_value=1, max_value=10)
    price = serializers.IntegerField(min_value=0)
    has_woman = serializers.BooleanField(default=False)
    status = serializers.ChoiceField(choices=TravelStatus.choices, required=False)

    class Meta:
        model = PassengerTravel
        fields = [
            'id', 'user', 'from_location', 'to_location',
            'travel_class', 'passenger', 'price', 'has_woman',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PassengerTravelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerTravel
        fields = [
            'user', 'from_location', 'to_location', 'travel_class',
            'passenger', 'price', 'has_woman'
        ]


class PassengerTravelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerTravel
        fields = [
            'user', 'from_location', 'to_location', 'travel_class',
            'passenger', 'price', 'has_woman', 'status'
        ]