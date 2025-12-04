# bot_app/serializers/driver.py
from rest_framework import serializers

from .bot_client import BotClientSerializer
from ..models import Driver, Car, DriverTransaction, BotClient


class DriverCarSerializer(serializers.ModelSerializer):
    """Driver ga tegishli carlarni olish uchun serializer"""

    class Meta:
        model = Car
        fields = [
            'id',
            'car_number',
            'car_model',
            'car_color'
        ]
        read_only_fields = ('created_at', 'updated_at')


class DriverWithCarsSerializer(serializers.ModelSerializer):
    """Driver va uning barcha carlari"""

    cars = DriverCarSerializer(many=True, read_only=True, source='driver')
    cars_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Driver
        fields = [
            'id',
            'telegram_id',
            'from_location',
            'to_location',
            'status',
            'profile_image',
            'status_display',
            'amount',
            'cars_count',
            'cars',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')
        ref_name = 'DriverWithCarsSerializer'  # Added ref_name

    def get_cars_count(self, obj):
        """Driverning carlari soni"""
        return obj.driver.count()


class DriverDetailSerializer(serializers.ModelSerializer):
    """Driver ning batafsil ma'lumotlari"""

    cars = DriverCarSerializer(many=True, read_only=True, source='driver')
    total_earnings = serializers.SerializerMethodField()
    active_cars_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Driver
        fields = [
            'id',
            'telegram_id',
            'from_location',
            'to_location',
            'status',
            "profile_image",
            'status_display',
            'amount',
            'total_earnings',
            'active_cars_count',
            'cars',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')
        ref_name = 'DriverDetailSerializer'  # Added ref_name

    def get_total_earnings(self, obj):
        """Driverning jami daromadi (transactions bo'yicha)"""
        from django.db.models import Sum
        total = DriverTransaction.objects.filter(
            driver=obj
        ).aggregate(total=Sum('amount'))['total']
        return total or 0

    def get_active_cars_count(self, obj):
        """Faol carlar soni (barcha carlar faol deb hisoblaymiz)"""
        return obj.driver.count()


class DriverTransactionSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.from_location', read_only=True)
    driver_telegram_id = serializers.SerializerMethodField()

    class Meta:
        model = DriverTransaction
        fields = '__all__'
        read_only_fields = ('created_at',)
        ref_name = 'DriverTransactionSerializer'  # Added ref_name

    def get_driver_telegram_id(self, obj):
        return obj.driver.telegram_id


class CarSerializer(serializers.ModelSerializer):
    driver_info = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
        ref_name = 'CarSerializer'  # Added ref_name

    def get_driver_info(self, obj):
        return {
            'id': obj.driver.id,
            'telegram_id': obj.driver.telegram_id,
            'from_location': obj.driver.from_location,
            'to_location': obj.driver.to_location
        }


class DriverSerializer(serializers.ModelSerializer):
    cars = DriverCarSerializer(many=True, read_only=True, source='driver')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Driver
        fields = [
            'id',
            "telegram_id",
            "full_name",
            "total_rides",
            "profile_image",
            "phone",
            "rating",
            "from_location",
            "to_location", "status",
            "amount",
            "cars",
            "status_display"
        ]
        ref_name = 'DriverMainSerializer'

class DriverListSerializer(serializers.ModelSerializer):
    cars_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    latest_car = serializers.SerializerMethodField()
    driver_info = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = [
            'id',
            'telegram_id',
            'from_location',
            'to_location',
            'status',
            "profile_image",
            'status_display',
            'amount',
            'cars_count',
            "driver_info",
            'latest_car',
            'created_at'
        ]
        ref_name = 'DriverListSerializer'  # Added ref_name

    def get_driver_info(self, obj):
        client = BotClient.objects.get(telegram_id=obj.telegram_id)
        return BotClientSerializer(client).data

    def get_cars_count(self, obj):
        return obj.driver.count()

    def get_latest_car(self, obj):
        """Eng so'ngi qo'shilgan car ma'lumoti"""
        latest_car = obj.driver.order_by('-created_at').first()
        if latest_car:
            return {
                'car_class': latest_car.car_class,
                'car_number': latest_car.car_number,
                'car_model': latest_car.car_model
            }
        return None

class DriverUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            'full_name',
            "phone",
            "rating",
            "profile_image",
            "from_location",
            "to_location",
            "amount",
            "total_rides"
        ]