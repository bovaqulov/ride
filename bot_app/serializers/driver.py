# bot_app/serializers/driver.py
from rest_framework import serializers
from ..models import Driver, Car, DriverTransaction


class DriverTransactionSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.from_location', read_only=True)

    class Meta:
        model = DriverTransaction
        fields = '__all__'
        read_only_fields = ('created_at',)


class CarSerializer(serializers.ModelSerializer):
    driver_info = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_driver_info(self, obj):
        return {
            'id': obj.driver.id,
            'from_location': obj.driver.from_location
        }


class DriverSerializer(serializers.ModelSerializer):
    cars = CarSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Driver
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    @classmethod
    def get_driver_by_telegram_id(cls, telegram_id):
        """Telegram ID bo'yicha driver olish (class method)"""
        try:
            return Driver.objects.get(telegram_id=telegram_id)
        except Driver.DoesNotExist:
            return None


class DriverListSerializer(serializers.ModelSerializer):
    cars_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Driver
        fields = ('id', 'user', 'from_location', 'to_location', 'status', 'status_display',
               'amount', 'cars_count', 'created_at')

    def get_cars_count(self, obj):
        return obj.cars.count()