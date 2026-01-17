from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count
from ..models import PassengerToDriverReview
from ..serializers.order_passenger_review import (
    PassengerToDriverReviewSerializer,
    PassengerToDriverReviewCreateSerializer,
    PassengerToDriverReviewUpdateSerializer
)


class PassengerToDriverReviewViewSet(viewsets.ModelViewSet):
    """
    PassengerToDriverReview uchun API endpoint
    """
    queryset = PassengerToDriverReview.objects.all().select_related('passenger', 'driver')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['passenger', 'driver', 'rate']
    search_fields = ['commit', 'passenger__full_name', 'order__id']
    ordering_fields = ['created_at', 'rate']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return PassengerToDriverReviewCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PassengerToDriverReviewUpdateSerializer
        return PassengerToDriverReviewSerializer

    def get_permissions(self):
        if self.action in ['destroy', 'update', 'partial_update']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Bir yolchi bir buyurtmaga faqat bir marta izoh qoldira olishi
        passenger_id = serializer.validated_data['passenger'].id
        driver_id = serializer.validated_data['driver'].id

        if PassengerToDriverReview.objects.filter(
                passenger_id=passenger_id,
                driver_id=driver_id
        ).exists():
            return Response(
                {'error': 'Bu buyurtma uchun allaqachon izoh qoldirgansiz'},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            PassengerToDriverReviewSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Umumiy statistika
        """
        total_reviews = self.get_queryset().count()
        average_rating = self.get_queryset().aggregate(
            avg_rating=Avg('rate')
        )['avg_rating'] or 0

        rating_distribution = self.get_queryset().values('rate').annotate(
            count=Count('rate')
        ).order_by('rate')

        return Response({
            'total_reviews': total_reviews,
            'average_rating': round(average_rating, 2),
            'rating_distribution': rating_distribution
        })

    @action(detail=False, methods=['get'])
    def by_driver(self, request):
        """
        Buyurtma bo'yicha izohlar
        """
        driver_id = request.query_params.get('driver_id')
        if not driver_id:
            return Response(
                {'error': 'driver_id parametri kerak'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reviews = self.get_queryset().filter(driver_id=driver_id)
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_passenger(self, request):
        """
        Yo'lovchi bo'yicha izohlar
        """
        passenger_id = request.query_params.get('passenger_id')
        if not passenger_id:
            return Response(
                {'error': 'passenger_id parametri kerak'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reviews = self.get_queryset().filter(passenger_id=passenger_id)
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)