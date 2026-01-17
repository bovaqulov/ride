# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

import logging

from ..models import Cashback, BotClient
from ..serializers.cashback import (
    CashbackSerializer
)

logger = logging.getLogger(__name__)


class CashbackViewSet(viewsets.ModelViewSet):
    """
    Cashback modeli uchun to'liq REST API
    """
    queryset = Cashback.objects.all()
    serializer_class = CashbackSerializer
    permission_classes = [IsAuthenticated]  # IsAuthenticated ga o'zgartiring
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Filter maydonlari
    filterset_fields = ['telegram_id', 'amount']

    # Qidirish maydonlari
    search_fields = ['telegram_id']

    # Tartiblash
    ordering_fields = ['telegram_id', 'amount',]


    @action(detail=False, methods=['get'], url_path='user/(?P<telegram_id>\d+)')
    def retrieve_by_telegram_id(self, request, telegram_id=None):
        """
        Telegram ID bo'yicha cashback olish
        GET /api/cashback/telegram/123456789/
        """
        try:
            cashback = Cashback.objects.get(telegram_id=telegram_id)
            serializer = self.get_serializer(cashback)
            return Response({
                'data': serializer.data
            })
        except Cashback.DoesNotExist:
            bot_client = BotClient.objects.filter(telegram_id=telegram_id)
            print(bot_client)
            if bot_client.exists():
                cashback = Cashback.objects.create(telegram_id=telegram_id)
                serializer = self.get_serializer(cashback)
                return Response({
                    'data': serializer.data
                })
            return Response({"error": "bu foydalanuvchi hali mavjud emas"})