from rest_framework import serializers
from bot_app.models import Tariff


class TariffSerializer(serializers.ModelSerializer):
    tariff_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = Tariff
        fields = ("tariff_id", "title", "translate")