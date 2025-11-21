# serializers.py
from rest_framework import serializers
from ..models import BotClient

class BotClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotClient
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class BotClientListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotClient
        fields = ('id', 'telegram_id', 'username', 'full_name', 'phone', 
                 'is_active', 'is_banned', 'total_rides', 'rating')

class BotClientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotClient
        fields = ('telegram_id', 'username', 'full_name', 'phone', 
                 'language', 'is_active', 'is_banned')

class BotClientUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotClient
        fields = ('username', 'full_name', 'phone', 'language', 
                 'is_active', 'is_banned', 'total_rides', 'rating')