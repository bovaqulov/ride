# services/location_service.py
import math
from typing import Dict, Any, List, Optional, Tuple
from asgiref.sync import sync_to_async
from ..models import City
from ..utils.nominatim_utils import aget_coords_from_place, aget_place_from_coords


class GlobalLocationService:

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formula bilan masofani hisoblash (km)"""
        R = 6371

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    @staticmethod
    async def get_city_coordinates(city_name: str, country: str = "uz") -> Optional[Tuple[float, float]]:
        """Shahar nomi bo'yicha koordinatalarni Nominatim orqali olish"""
        try:
            results = await aget_coords_from_place(city_name, country_code=country, limit=1)
            if results and results[0].get('lat') and results[0].get('lon'):
                return results[0]['lat'], results[0]['lon']
        except Exception:
            pass
        return None

    @staticmethod
    async def is_location_in_city_area(
        lat: float,
        lon: float,
        city: City,
        max_distance_km: float = 20.0
    ) -> Tuple[bool, float, Dict[str, Any], Dict[str, Any]]:
        """
        Koordinata shahar hududida ekanligini tekshirish
        """
        # Shaharning koordinatalarini olish
        city_coords = await GlobalLocationService.get_city_coordinates(city.title)
        address_info = await aget_place_from_coords(lat, lon)

        if not city_coords:
            return False, 0, address_info, {}

        city_lat, city_lon = city_coords
        distance = GlobalLocationService.calculate_distance(lat, lon, city_lat, city_lon)

        # Shahar ma'lumotlarini olish
        city_address_info = await aget_place_from_coords(city_lat, city_lon)

        # Hududni tekshirish
        is_in_city = (
            distance <= max_distance_km and
            address_info.get('shahar_tuman') == city_address_info.get('shahar_tuman')
        )

        return is_in_city, distance, address_info, city_address_info

    @staticmethod
    async def find_city_for_location(
        lat: float,
        lon: float,
        max_distance_km: float = 50.0
    ) -> Tuple[Optional[City], float, Dict[str, Any]]:
        """
        Koordinata uchun mos shaharni topish
        """
        address_info = await aget_place_from_coords(lat, lon)
        location_city_name = address_info.get('shahar_tuman')

        if not location_city_name:
            return None, 0, address_info

        # Barcha ruxsat etilgan shaharlarni olish (asinxron)
        @sync_to_async
        def get_allowed_cities():
            return list(City.objects.filter(is_allowed=True))

        cities = await get_allowed_cities()

        best_match = None
        min_distance = float('inf')

        for city in cities:
            # Nomlar mos kelishini tekshirish
            if (city.title.lower() in location_city_name.lower() or
                    location_city_name.lower() in city.title.lower()):

                # Aniq koordinatalarni tekshirish
                city_coords = await GlobalLocationService.get_city_coordinates(city.title)
                if city_coords:
                    distance = GlobalLocationService.calculate_distance(
                        lat, lon, city_coords[0], city_coords[1]
                    )

                    if distance <= max_distance_km and distance < min_distance:
                        min_distance = distance
                        best_match = city

        return best_match, min_distance, address_info

    @staticmethod
    async def validate_city_location(
        city_name: str,
        lat: float,
        lon: float,
        max_distance_km: float = 20.0
    ) -> Dict[str, Any]:
        """
        Shahar nomi va koordinatalar mos kelishini tekshirish
        """
        # Shahar koordinatalarini olish
        city_coords = await GlobalLocationService.get_city_coordinates(city_name)

        if not city_coords:
            return {
                "valid": False,
                "error": f"{city_name} shahri uchun koordinatalar topilmadi",
                "distance_km": None
            }

        # Masofani hisoblash
        distance = GlobalLocationService.calculate_distance(lat, lon, city_coords[0], city_coords[1])

        # Hudud ma'lumotlarini olish
        user_address = await aget_place_from_coords(lat, lon)
        city_address = await aget_place_from_coords(city_coords[0], city_coords[1])

        is_valid = distance <= max_distance_km

        return {
            "valid": is_valid,
            "distance_km": distance,
            "max_distance_km": max_distance_km,
            "city_coordinates": {"lat": city_coords[0], "lon": city_coords[1]},
            "user_location": user_address,
            "city_location": city_address,
            "message": f"Koordinatalar {city_name} shahar hududida {'bor' if is_valid else 'yoq'}. Masofa: {distance:.1f} km"
        }

    @staticmethod
    async def search_cities_by_location(
        lat: float,
        lon: float,
        max_distance_km: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        Berilgan lokatsiya atrofidagi shaharlarni topish
        """
        address_info = await aget_place_from_coords(lat, lon)
        location_city_name = address_info.get('shahar_tuman', '')

        # Barcha ruxsat etilgan shaharlarni olish (asinxron)
        @sync_to_async
        def get_allowed_cities():
            return list(City.objects.filter(is_allowed=True))

        cities = await get_allowed_cities()
        results = []

        for city in cities:
            city_coords = await GlobalLocationService.get_city_coordinates(city.title)
            if city_coords:
                distance = GlobalLocationService.calculate_distance(
                    lat, lon, city_coords[0], city_coords[1]
                )

                if distance <= max_distance_km:
                    results.append({
                        "city": city,
                        "distance_km": distance,
                        "coordinates": {"lat": city_coords[0], "lon": city_coords[1]},
                        "match_type": "distance"
                    })

        # Nom bo'yicha qo'shimcha qidiruv
        if location_city_name:
            for city in cities:
                if (city.title.lower() in location_city_name.lower() or
                        location_city_name.lower() in city.title.lower()):

                    # Agar allaqachon qo'shilgan bo'lsa, o'tkazib yuboramiz
                    if not any(r["city"].id == city.pk for r in results):
                        city_coords = await GlobalLocationService.get_city_coordinates(city.title)
                        distance = GlobalLocationService.calculate_distance(
                            lat, lon, city_coords[0], city_coords[1]
                        ) if city_coords else float('inf')

                        results.append({
                            "city": city,
                            "distance_km": distance,
                            "coordinates": {"lat": city_coords[0], "lon": city_coords[1]} if city_coords else None,
                            "match_type": "name"
                        })

        # Masofa bo'yicha saralash
        results.sort(key=lambda x: x["distance_km"])
        return results