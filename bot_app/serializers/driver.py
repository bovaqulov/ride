# bot_app/serializers/driver.py
from rest_framework import serializers

from .bot_client import BotClientSerializer
from ..models import Driver, Car, DriverTransaction, BotClient, DriverGallery


class DriverGallerySerializer(serializers.ModelSerializer):
    """DriverGallery modeli uchun serializer"""

    class Meta:
        model = DriverGallery
        fields = ['profile_image']
        read_only_fields = ['profile_image']


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
    profile_image = serializers.SerializerMethodField()  # Yangi qo'shildi

    class Meta:
        model = Driver
        fields = [
            'id',
            'telegram_id',
            'from_location',
            'to_location',
            'status',
            'status_display',
            'amount',
            'cars_count',
            'cars',
            'profile_image',  # Yangi qo'shildi
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')
        ref_name = 'DriverWithCarsSerializer'

    def get_cars_count(self, obj):
        """Driverning carlari soni"""
        return obj.driver.count()

    def get_profile_image(self, obj):
        """Driverning profile rasmini olish"""
        try:
            gallery = DriverGallery.objects.get(telegram_id=obj)
            if gallery.profile_image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(gallery.profile_image.url)
                return gallery.profile_image.url
        except DriverGallery.DoesNotExist:
            pass
        return None


class DriverDetailSerializer(serializers.ModelSerializer):
    """Driver ning batafsil ma'lumotlari"""

    cars = DriverCarSerializer(many=True, read_only=True, source='driver')
    total_earnings = serializers.SerializerMethodField()
    active_cars_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    profile_image = serializers.SerializerMethodField()  # Yangi qo'shildi
    gallery_info = serializers.SerializerMethodField()  # Barcha gallery ma'lumotlari uchun

    class Meta:
        model = Driver
        fields = [
            'id',
            'telegram_id',
            'from_location',
            'to_location',
            'status',
            'status_display',
            'amount',
            'total_earnings',
            'active_cars_count',
            'cars',
            'profile_image',  # Yangi qo'shildi
            'gallery_info',  # Yangi qo'shildi
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')
        ref_name = 'DriverDetailSerializer'

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

    def get_profile_image(self, obj):
        """Driverning profile rasmini olish"""
        try:
            gallery = DriverGallery.objects.get(telegram_id=obj)
            if gallery.profile_image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(gallery.profile_image.url)
                return gallery.profile_image.url
        except DriverGallery.DoesNotExist:
            pass
        return None

    def get_gallery_info(self, obj):
        """DriverGallery ning barcha ma'lumotlari"""
        try:
            gallery = DriverGallery.objects.get(telegram_id=obj)
            return DriverGallerySerializer(gallery).data
        except DriverGallery.DoesNotExist:
            return None


class DriverTransactionSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.from_location', read_only=True)
    driver_telegram_id = serializers.SerializerMethodField()
    driver_profile_image = serializers.SerializerMethodField()  # Yangi qo'shildi

    class Meta:
        model = DriverTransaction
        fields = '__all__'
        read_only_fields = ('created_at',)
        ref_name = 'DriverTransactionSerializer'

    def get_driver_telegram_id(self, obj):
        return obj.driver.telegram_id

    def get_driver_profile_image(self, obj):
        """Transaction uchun driverning rasmi"""
        try:
            gallery = DriverGallery.objects.get(telegram_id=obj.driver)
            if gallery.profile_image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(gallery.profile_image.url)
                return gallery.profile_image.url
        except DriverGallery.DoesNotExist:
            pass
        return None


class CarSerializer(serializers.ModelSerializer):
    driver_info = serializers.SerializerMethodField()
    driver_profile_image = serializers.SerializerMethodField()  # Yangi qo'shildi

    class Meta:
        model = Car
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
        ref_name = 'CarSerializer'

    def get_driver_info(self, obj):
        return {
            'id': obj.driver.id,
            'telegram_id': obj.driver.telegram_id,
            'from_location': obj.driver.from_location,
            'to_location': obj.driver.to_location
        }

    def get_driver_profile_image(self, obj):
        """Car uchun driverning rasmi"""
        try:
            gallery = DriverGallery.objects.get(telegram_id=obj.driver)
            if gallery.profile_image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(gallery.profile_image.url)
                return gallery.profile_image.url
        except DriverGallery.DoesNotExist:
            pass
        return None


class DriverSerializer(serializers.ModelSerializer):
    cars = DriverCarSerializer(many=True, read_only=True, source='driver')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    profile_image = serializers.SerializerMethodField()  # Yangi qo'shildi
    full_profile_image_url = serializers.SerializerMethodField()  # To'liq URL uchun

    class Meta:
        model = Driver
        fields = [
            'id',
            "telegram_id",
            "full_name",
            "total_rides",
            "phone",
            "rating",
            "from_location",
            "to_location",
            "status",
            "amount",
            "cars",
            "status_display",
            "profile_image",  # Yangi qo'shildi
            "full_profile_image_url"  # Yangi qo'shildi
        ]
        ref_name = 'DriverMainSerializer'

    def get_profile_image(self, obj):
        """Driverning profile rasmini olish (relative path)"""
        try:
            gallery = DriverGallery.objects.get(telegram_id=obj)
            return gallery.profile_image.path if gallery.profile_image else None
        except DriverGallery.DoesNotExist:
            return None

    def get_full_profile_image_url(self, obj):
        """Driverning profile rasmini to'liq URL sifatida olish"""
        try:
            gallery = DriverGallery.objects.get(telegram_id=obj)
            if gallery.profile_image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(gallery.profile_image.path)
                return gallery.profile_image.url
        except DriverGallery.DoesNotExist:
            pass
        return None


class DriverListSerializer(serializers.ModelSerializer):
    cars_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    latest_car = serializers.SerializerMethodField()
    driver_info = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()  # Yangi qo'shildi

    class Meta:
        model = Driver
        fields = [
            'id',
            'telegram_id',
            'from_location',
            'to_location',
            'status',
            'status_display',
            'amount',
            'cars_count',
            "driver_info",
            'latest_car',
            'profile_image',  # Yangi qo'shildi
            'created_at'
        ]
        ref_name = 'DriverListSerializer'

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

    def get_profile_image(self, obj):
        """Driverning profile rasmini olish"""
        try:
            gallery = DriverGallery.objects.get(telegram_id=obj)
            if gallery.profile_image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(gallery.profile_image.url)
                return gallery.profile_image.url
        except DriverGallery.DoesNotExist:
            pass
        return None


class DriverUpdateSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(write_only=True, required=False)  # Yangi qo'shildi
    current_profile_image = serializers.SerializerMethodField(read_only=True)  # Yangi qo'shildi

    class Meta:
        model = Driver
        fields = [
            'full_name',
            "phone",
            "rating",
            "from_location",
            "to_location",
            "amount",
            'status',
            "total_rides",
            "profile_image",  # Yangi qo'shildi
            "current_profile_image"  # Yangi qo'shildi
        ]

    def get_current_profile_image(self, obj):
        """Joriy profile rasmni olish"""
        try:
            gallery = DriverGallery.objects.get(telegram_id=obj)
            if gallery.profile_image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(gallery.profile_image.url)
                return gallery.profile_image.url
        except DriverGallery.DoesNotExist:
            pass
        return None

    def update(self, instance, validated_data):
        """Driver ma'lumotlarini yangilash va rasmni saqlash"""
        profile_image = validated_data.pop('profile_image', None)

        # Driver ma'lumotlarini yangilash
        driver = super().update(instance, validated_data)

        # Agar rasm berilgan bo'lsa, DriverGallery ni yangilash yoki yaratish
        if profile_image:
            gallery, created = DriverGallery.objects.get_or_create(
                telegram_id=driver,
                defaults={'profile_image': profile_image}
            )
            if not created:
                gallery.profile_image = profile_image
                gallery.save()

        return driver


class DriverCreateSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(write_only=True, required=False)  # Yangi qo'shildi

    class Meta:
        model = Driver
        fields = [
            'telegram_id',
            'full_name',
            'phone',
            'from_location',
            'to_location',
            'status',
            'amount',
            'profile_image'  # Yangi qo'shildi
        ]

    def create(self, validated_data):
        """Driver yaratish va rasmni saqlash"""
        profile_image = validated_data.pop('profile_image', None)

        # Driver ni yaratish
        driver = Driver.objects.create(**validated_data)

        # Agar rasm berilgan bo'lsa, DriverGallery ni yaratish
        if profile_image:
            DriverGallery.objects.create(
                telegram_id=driver,
                profile_image=profile_image
            )

        return driver