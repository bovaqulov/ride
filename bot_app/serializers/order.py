# serializers.py
import logging

from django.db.models import Q
import json
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder

from .driver import DriverSerializer
from .passenger import PassengerSerializer
from .bot_client import BotClientSerializer
from .route import RouteSerializer
from .tariff_serializer import TariffSerializer
from ..models import Order, OrderType, Driver, BotClient, Passenger, CityPrice, Tariff, PassengerTravel, PassengerPost, \
    PassengerReject, PassengerToDriverReview, Route

logger = logging.getLogger(__name__)

class ContentObjectSerializer(serializers.Serializer):
    """Generic content object serializer"""

    def to_representation(self, instance):
        route_id = instance.route.id if getattr(instance, "route", None) else None
        tariff_id = instance.tariff.id if getattr(instance, "tariff", None) else None

        price = CityPrice.objects.filter(Q(tariff=tariff_id) & Q(route=route_id)).first()
        if price:
            price = price.price
        else:
            price = None

        if tariff_id:
            tariff = TariffSerializer(Tariff.objects.filter(id=tariff_id).first(), many=False).data
        else:
            tariff = None

        data = {
            "id": instance.pk,
            "price": price,
            "route_id": route_id,
            "tariff": tariff,
            "from_location": instance.from_location,
            "to_location": instance.to_location,
            "cashback": instance.cashback,
            "comment": instance.comment,
            "start_time": instance.start_time,
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
        }

        if isinstance(instance, PassengerTravel):
            extra = {
                "type": "passengertravel",
                "passenger": instance.passenger,
                "has_woman": instance.has_woman,
            }
            return {**data, **extra}

        if isinstance(instance, PassengerPost):
            extra = {
                "type": "passengerpost",
            }
            return {**data, **extra}

        return None

    def get_serialized_data(self, instance):
        """JSON serializatsiya uchun maxsus metod"""
        data = self.to_representation(instance)
        return json.loads(json.dumps(data, cls=DjangoJSONEncoder))

class ContentObject2Serializer(serializers.Serializer):
        """Generic content object serializer"""

        def to_representation(self, instance):
            route_id = instance.route.id if getattr(instance, "route", None) else None
            tariff_id = instance.tariff.id if getattr(instance, "tariff", None) else None
            price = CityPrice.objects.filter(Q(tariff=tariff_id) & Q(route=route_id)).first()

            logger.warning(price)


            if price:
                price = price.price
            else:
                price = None


            if route_id:
                route = RouteSerializer(Route.objects.filter(id=route_id).first()).data
            else:
                route = {}

            data = {
                "price": price,
                "route": route,
                "tariff_id": tariff_id,
                "from_location": instance.from_location,
                "to_location": instance.to_location,
                "cashback": instance.cashback,
                "comment": instance.comment,
                "start_time": instance.start_time.isoformat() if instance.start_time else None,
                "created_at": instance.created_at.isoformat() if instance.created_at else None,
            }

            if isinstance(instance, PassengerTravel):
                extra = {
                    "passenger": instance.passenger,
                    "has_woman": instance.has_woman,
                }
                return {**data, **extra}

            if isinstance(instance, PassengerPost):
                return data
            return None


class DriverOrderSerializer(serializers.ModelSerializer):
    content_object = ContentObject2Serializer(read_only=True)
    creator = serializers.SerializerMethodField()
    driver_details = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'creator', 'status', "driver_details",
            'order_type', 'content_object',
        ]
        read_only_fields = ['id', 'content_object']

    def get_creator(self, obj):
        try:
            creator = Passenger.objects.get(telegram_id=obj.user)
            return PassengerSerializer(creator).data
        except Exception as e:
            print("orderserializer error: ", str(e))
            return {}

    def get_driver_details(self, obj):
        try:
            driver = Driver.objects.get(id=obj.driver.id)
            return DriverSerializer(driver).data
        except Exception as e:
            return None



class OrderSerializer(serializers.ModelSerializer):
    content_object = ContentObjectSerializer(read_only=True)
    driver_details = DriverSerializer(source='driver', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    creator = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'creator', 'driver', 'driver_details', 'status',
            'order_type', 'content_object', 'content_type_name',
        ]
        read_only_fields = ['id', 'content_object']

    def get_creator(self, obj):
        try:
            creator = Passenger.objects.get(telegram_id=obj.user)
            return PassengerSerializer(creator).data
        except Exception as e:
            print("orderserializer error: ", str(e))
            return {}

    def to_representation(self, instance):
        """Override to handle datetime serialization"""
        representation = super().to_representation(instance)

        # Datetime fieldlarni ISO formatga o'tkazish
        if representation.get('created_at'):
            representation['created_at'] = instance.created_at.isoformat()

        if representation.get('updated_at'):
            representation['updated_at'] = instance.updated_at.isoformat()

        # Content objectni serializatsiya qilish
        if instance.content_object:
            content_serializer = ContentObjectSerializer()
            representation['content_object'] = content_serializer.get_serialized_data(instance.content_object)

        return representation


class OrderCreateSerializer(serializers.ModelSerializer):
    content_type = serializers.ChoiceField(
        choices=['passengertravel', 'passengerpost'],
        write_only=True
    )
    object_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = ['user', 'order_type', 'content_type', 'object_id']

    def validate(self, attrs):
        content_type_name = attrs.get('content_type')
        object_id = attrs.get('object_id')
        order_type = attrs.get('order_type')

        # Content type va object mavjudligini tekshirish
        try:
            content_type = ContentType.objects.get(model=content_type_name)
            model_class = content_type.model_class()
            obj = model_class.objects.get(id=object_id)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError({
                'content_type': 'Noto\'g\'ri content type'
            })
        except model_class.DoesNotExist:
            raise serializers.ValidationError({
                'object_id': f'{content_type_name} topilmadi'
            })

        # Order type va content type mos kelishini tekshirish
        if (order_type == OrderType.TRAVEL and
                content_type_name != 'passengertravel'):
            raise serializers.ValidationError({
                'order_type': 'Travel order faqat PassengerTravel ga bog\'lanishi kerak'
            })
        elif (order_type == OrderType.DELIVERY and
              content_type_name != 'passengerpost'):
            raise serializers.ValidationError({
                'order_type': 'Delivery order faqat PassengerPost ga bog\'lanishi kerak'
            })

        return attrs

    def create(self, validated_data):
        content_type_name = validated_data.pop('content_type')
        object_id = validated_data.pop('object_id')

        content_type = ContentType.objects.get(model=content_type_name)

        return Order.objects.create(
            **validated_data,
            content_type=content_type,
            object_id=object_id
        )


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['driver', 'status']


class OrderListSerializer(serializers.ModelSerializer):
    driver_details = serializers.SerializerMethodField()
    content_object = ContentObjectSerializer(read_only=True)
    creator = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'creator', 'content_object', 'driver', 'driver_details', 'status', 'order_type', 'object_id',
        ]

    def get_driver_details(self, obj):
        try:
            driver = Driver.objects.get(id=obj.driver.id)
            return DriverSerializer(driver).data
        except Exception as e:
            return None

    def get_creator(self, obj):
        try:
            creator = BotClient.objects.get(telegram_id=obj.user)
            return BotClientSerializer(creator).data
        except Exception as e:
            print("order list error: ", e)
            return {}


class PassengerRejectCreateSerializer(serializers.ModelSerializer):
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        source="order",
        write_only=True
    )

    class Meta:
        model = PassengerReject
        fields = ["order_id", "comment"]

class PassengerToDriverReviewCreateSerializer(serializers.ModelSerializer):
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        source="order",
        write_only=True
    )
    passenger_id = serializers.PrimaryKeyRelatedField(
        queryset=Passenger.objects.all(),
        source="passenger",
        write_only=True
    )

    class Meta:
        model = PassengerToDriverReview
        fields = ["order_id", "passenger_id", "comment", "rate", "feedback"]

    def validate(self, attrs):
        order = attrs.get("order")
        passenger = attrs.get("passenger")
        rate = attrs.get("rate")

        # rate nazorati (choices bor, lekin aniq xabar uchun)
        if rate is not None and rate not in [1, 2, 3, 4, 5]:
            raise serializers.ValidationError({"rate": "Rate 1 dan 5 gacha bo‘lishi kerak."})

        # order driverga biriktirilganmi?
        if order and not getattr(order, "driver_id", None):
            raise serializers.ValidationError({"order_id": "Bu orderda driver hali biriktirilmagan."})

        # order shu passenger’ga tegishlimi? (sizning Order.user = telegram_id bo‘lsa)
        # Eslatma: Passenger modelingizda telegram_id bormi deb shunga moslab yozdim.
        if order and passenger:
            if getattr(passenger, "telegram_id", None) != getattr(order, "user", None):
                raise serializers.ValidationError({"order_id": "Bu order sizga tegishli emas."})

        # duplicate review’ni oldindan ushlash (DB constraint bilan ham ushlanadi)
        if order and passenger:
            exists = PassengerToDriverReview.objects.filter(order=order, passenger=passenger).exists()
            if exists:
                raise serializers.ValidationError("Bu order uchun review allaqachon yozilgan.")

        return attrs
