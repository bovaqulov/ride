from rest_framework import viewsets

from ..models import Tariff
from ..serializers.tariff_serializer import TariffSerializer


class TariffViewSet(viewsets.ModelViewSet):
    queryset = Tariff.objects.all()
    serializer_class = TariffSerializer

