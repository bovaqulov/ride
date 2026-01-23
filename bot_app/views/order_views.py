# views.py
from django.db import transaction
from rest_framework import viewsets, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Order
from ..serializers.order import (
    OrderSerializer, OrderCreateSerializer, OrderUpdateSerializer, OrderListSerializer, PassengerRejectCreateSerializer,
    PassengerToDriverReviewCreateSerializer, DriverOrderSerializer,
)
from ..filters.order_filters import OrderFilter


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related(
        'driver', 'content_type'
    )
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OrderFilter
    search_fields = ['user', 'driver__name', 'content_type__model']
    ordering_fields = [
        'id', 'user', 'status', 'order_type',
        'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        elif self.action == 'list':
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Dynamic filtering based on query parameters
        status_list = self.request.query_params.get('status_list')
        if status_list:
            statuses = status_list.split(',')
            queryset = queryset.filter(status__in=statuses)

        # Order type list filter
        order_type_list = self.request.query_params.get('order_type_list')
        if order_type_list:
            types = order_type_list.split(',')
            queryset = queryset.filter(order_type__in=types)

        return queryset

    @action(detail=False, methods=['get'], url_path="user/(?P<telegram_id>[^/.]+)")
    def by_telegram_id(self, request, telegram_id=None):
        try:
            telegram_id = int(telegram_id)
            order = Order.objects.filter(user=telegram_id)
            serializer = OrderListSerializer(order, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            return Response(
                {'error': 'Noto\'g\'ri telegram ID formati'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Order.DoesNotExist:
            return Response(
                {'error': 'Foydalanuvchi topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'], url_path="reject")
    def reject(self, request):
        try:

            serializer = PassengerRejectCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                reject_obj = serializer.save()

                order = reject_obj.order
                order.status = "rejected"
                order.save(update_fields=["status"])

            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path="review")
    def review(self, request):
        try:
            serializer = PassengerToDriverReviewCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                review_obj = serializer.save()

            return Response(
                {"message": "success", "id": review_obj.id},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path="driver")
    def driver(self, request, pk=None):
        try:
            orders = Order.objects.get(id=pk)
            serializer = DriverOrderSerializer(orders).data
            return Response(serializer, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)