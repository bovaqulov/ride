from django.db.models import Exists, OuterRef
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response

from ..models import Route, City
from ..serializers.route import RoutePriceOptimizedSerializer, CitySimpleSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.filter(is_active=True)
    serializer_class = RoutePriceOptimizedSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['from_city', 'to_city']
    search_fields = ['from_city', 'to_city']
    ordering_fields = ['from_city', 'to_city']
    ordering = ['from_city']

    @action(detail=False, methods=['get'], url_path='from-city/(?P<city_id>\d+)')
    def get_routes_from_city(self, request, city_id=None):
        try:
            city = City.objects.get(id=city_id)

            routes = Route.objects.filter(from_city=city, is_active=True)

            return Response({
                'target': RoutePriceOptimizedSerializer(routes, many=True).data,
            })

        except City.DoesNotExist:
            return Response(
                {'error': f'Shahar topilmadi (ID: {city_id})'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='from-cities')
    def get_routes_from_cities(self, request):
        try:
            cities = City.objects.filter(
                Exists(
                    Route.objects.filter(
                        is_active=True,
                        from_city=OuterRef('pk')
                    )
                )
            )
            return Response(
                {'cities': CitySimpleSerializer(cities, many=True).data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )