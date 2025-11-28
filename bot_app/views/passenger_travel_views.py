# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from ..filters.passenger_travel_filter import PassengerTravelFilter
from ..models import PassengerTravel, TravelStatus
from ..serializers.passenger_travel import (
    PassengerTravelSerializer,
    PassengerTravelCreateSerializer,
    PassengerTravelUpdateSerializer
)


class PassengerTravelViewSet(viewsets.ModelViewSet):
    queryset = PassengerTravel.objects.all()
    filterset_class = PassengerTravelFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'user', 'travel_class', 'status', 'has_woman'
    ]
    search_fields = [
        'from_location', 'to_location'
    ]
    ordering_fields = [
        'price', 'passenger', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return PassengerTravelCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PassengerTravelUpdateSerializer
        return PassengerTravelSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        full_serializer = PassengerTravelSerializer(instance)

        return Response(full_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Custom action to update travel status"""
        travel = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status not in dict(TravelStatus.choices):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        travel.status = new_status
        travel.save()

        serializer = self.get_serializer(travel)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Get travels by specific user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        travels = PassengerTravel.objects.filter(user=user_id)
        serializer = self.get_serializer(travels, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search_routes(self, request):
        """Search for travels by from and to locations"""
        from_loc = request.query_params.get('from')
        to_loc = request.query_params.get('to')

        queryset = self.filter_queryset(self.get_queryset())

        if from_loc:
            queryset = queryset.filter(from_location__icontains=from_loc)
        if to_loc:
            queryset = queryset.filter(to_location__icontains=to_loc)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)