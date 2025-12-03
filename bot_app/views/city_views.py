# views.py
from asgiref.sync import async_to_sync, sync_to_async
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from ..models import City
from ..serializers.city import (
    CitySerializer,
    CityCreateSerializer,
    LocationCheckSerializer,
    LocationCheckResponseSerializer,
    CityValidationSerializer,
    CityValidationResponseSerializer,
    NearbyCitiesResponseSerializer
)
from ..services.location_service import GlobalLocationService


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_allowed', 'subcategory']
    search_fields = ['title']
    ordering_fields = ['title', 'created_at', 'updated_at']
    ordering = ['title']

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return CityCreateSerializer
        return CitySerializer

    def create(self, request, *args, **kwargs):
        """Sync wrapper for async create"""
        return async_to_sync(self._async_create)(request, *args, **kwargs)

    async def _async_create(self, request, *args, **kwargs):
        """Async create logic"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Location tekshiruvi
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        city_title = request.data.get('title')
        skip_validation = request.data.get('skip_location_validation', False)

        if latitude and longitude and city_title and not skip_validation:
            validation_result = await GlobalLocationService.validate_city_location(
                city_title, latitude, longitude
            )

            if not validation_result["valid"]:
                return Response({
                    "error": "location_validation_failed",
                    "message": validation_result["message"],
                    "details": validation_result
                }, status=status.HTTP_400_BAD_REQUEST)

        city = await sync_to_async(serializer.save)()
        response_serializer = CitySerializer(city)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Sync wrapper for async update"""
        return async_to_sync(self._async_update)(request, *args, **kwargs)

    async def _async_update(self, request, *args, **kwargs):
        """Async update logic"""
        instance = await sync_to_async(self.get_object)()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        city_title = request.data.get('title', instance.title)
        skip_validation = request.data.get('skip_location_validation', False)

        if latitude and longitude and not skip_validation:
            validation_result = await GlobalLocationService.validate_city_location(
                city_title, latitude, longitude
            )

            if not validation_result["valid"]:
                return Response({
                    "error": "location_validation_failed",
                    "message": validation_result["message"],
                    "details": validation_result
                }, status=status.HTTP_400_BAD_REQUEST)

        city = await sync_to_async(serializer.save)()
        response_serializer = CitySerializer(city)
        return Response(response_serializer.data)

    @action(detail=False, methods=['post'], url_path='check-location')
    def check_location(self, request):
        """Sync wrapper for async check_location"""
        return async_to_sync(self._async_check_location)(request)

    async def _async_check_location(self, request):
        """Koordinatalar shahar hududida ekanligini tekshirish"""
        serializer = LocationCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lat = serializer.validated_data['latitude']
        lon = serializer.validated_data['longitude']
        max_distance = serializer.validated_data['max_distance_km']

        city, distance, address_info = await GlobalLocationService.find_city_for_location(
            lat, lon, max_distance
        )

        if city:
            response_data = {
                "is_in_city": True,
                "city": CitySerializer(city).data,
                "distance_km": round(distance, 2),
                "address_info": address_info,
                "message": f"Koordinatalar {city.title} shahar hududida. Masofa: {distance:.1f} km",
                "match_type": "exact"
            }
        else:
            nearby_cities = await GlobalLocationService.search_cities_by_location(lat, lon, max_distance)
            if nearby_cities:
                nearest_city = nearby_cities[0]
                response_data = {
                    "is_in_city": False,
                    "city": CitySerializer(nearest_city["city"]).data,
                    "distance_km": round(nearest_city["distance_km"], 2),
                    "address_info": address_info,
                    "message": f"Koordinatalar hech qanday shahar hududida emas. Eng yaqin shahar: {nearest_city['city'].title} ({nearest_city['distance_km']:.1f} km)",
                    "match_type": "nearest"
                }
            else:
                response_data = {
                    "is_in_city": False,
                    "address_info": address_info,
                    "message": "Koordinatalar hech qanday shahar hududida emas va yaqin shaharlar topilmadi",
                    "match_type": "none"
                }

        response_serializer = LocationCheckResponseSerializer(response_data)
        return Response(response_serializer.data)

    @action(detail=False, methods=['post'], url_path='validate-city-location')
    def validate_city_location(self, request):
        """Sync wrapper for async validate_city_location"""
        return async_to_sync(self._async_validate_city_location)(request)

    async def _async_validate_city_location(self, request):
        """Shahar nomi va koordinatalar mos kelishini tekshirish"""
        serializer = CityValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        city_name = serializer.validated_data['city_name']
        lat = serializer.validated_data['latitude']
        lon = serializer.validated_data['longitude']

        validation_result = await GlobalLocationService.validate_city_location(city_name, lat, lon)

        response_serializer = CityValidationResponseSerializer(validation_result)
        return Response(response_serializer.data)

    @action(detail=False, methods=['post'], url_path='nearby-cities')
    def nearby_cities(self, request):
        """Sync wrapper for async nearby_cities"""
        return async_to_sync(self._async_nearby_cities)(request)

    async def _async_nearby_cities(self, request):
        """Berilgan lokatsiya atrofidagi shaharlarni topish"""
        serializer = LocationCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lat = serializer.validated_data['latitude']
        lon = serializer.validated_data['longitude']
        max_distance = serializer.validated_data['max_distance_km']

        nearby_cities = await GlobalLocationService.search_cities_by_location(lat, lon, max_distance)

        results = []
        for city_data in nearby_cities:
            results.append({
                "city": CitySerializer(city_data["city"]).data,
                "distance_km": round(city_data["distance_km"], 2),
                "coordinates": city_data.get("coordinates"),
                "match_type": city_data["match_type"]
            })

        response_serializer = NearbyCitiesResponseSerializer(results, many=True)
        return Response(response_serializer.data)

    @action(detail=True, methods=['get'], url_path='location-info')
    def get_city_location_info(self, request, pk=None):
        """Sync wrapper for async get_city_location_info"""
        return async_to_sync(self._async_get_city_location_info)(request, pk)

    async def _async_get_city_location_info(self, request, pk=None):
        """Shahar uchun lokatsiya ma'lumotlarini olish"""
        city = await sync_to_async(self.get_object)()

        city_coords = await GlobalLocationService.get_city_coordinates(city.title)
        if not city_coords:
            return Response({
                "error": "Shahar uchun lokatsiya ma'lumotlari topilmadi"
            }, status=status.HTTP_404_NOT_FOUND)

        # get_place_from_coords_sync ichida asyncio.run() bor, shuning uchun uni
        # to'g'ridan-to'g'ri aget_place_from_coords bilan almashtirish kerak
        from ..utils.nominatim_utils import aget_place_from_coords
        address_info = await aget_place_from_coords(city_coords[0], city_coords[1])

        return Response({
            "city": CitySerializer(city).data,
            "coordinates": {
                "latitude": city_coords[0],
                "longitude": city_coords[1]
            },
            "address_info": address_info
        })

    @action(detail=False, methods=['get'], url_path='search-by-name')
    def search_cities_by_name(self, request):
        """Sync wrapper for async search_cities_by_name"""
        return async_to_sync(self._async_search_cities_by_name)(request)

    async def _async_search_cities_by_name(self, request):
        """Shahar nomi bo'yicha qidirish va koordinatalarni olish"""
        city_name = request.query_params.get('name')
        if not city_name:
            return Response({
                "error": "name parametri talab qilinadi"
            }, status=status.HTTP_400_BAD_REQUEST)

        @sync_to_async
        def get_cities():
            return list(City.objects.filter(
                Q(title__icontains=city_name) |
                Q(title__iexact=city_name),
                is_allowed=True
            ))

        cities = await get_cities()

        results = []
        for city in cities:
            city_coords = await GlobalLocationService.get_city_coordinates(city.title)
            results.append({
                "city": CitySerializer(city).data,
                "coordinates": {
                    "latitude": city_coords[0],
                    "longitude": city_coords[1]
                } if city_coords else None,
                "has_coordinates": city_coords is not None
            })

        return Response(results)