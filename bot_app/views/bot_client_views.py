# views.py

from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ..models import BotClient
from ..serializers.bot_client import BotClientCreateSerializer, BotClientUpdateSerializer, BotClientListSerializer, \
    BotClientSerializer
from ..filters.bot_client_filters import BotClientFilter


class BotClientViewSet(viewsets.ModelViewSet):
    queryset = BotClient.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BotClientFilter
    search_fields = ['full_name', 'username', 'phone']
    ordering_fields = ['created_at', 'updated_at', 'total_rides', 'rating']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return BotClientCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BotClientUpdateSerializer
        elif self.action == 'list':
            return BotClientListSerializer
        return BotClientSerializer

    def get_queryset(self):
        """Return base queryset"""
        return BotClient.objects.all()

    def get_object(self):
        """Get object by telegram_id if 'pk' is provided as telegram_id"""
        # Check if we're looking up by telegram_id instead of primary key
        if 'pk' in self.kwargs and str(self.kwargs['pk']).isdigit():
            pk = int(self.kwargs['pk'])
            # Try to find by telegram_id first
            try:
                return BotClient.objects.get(telegram_id=pk)
            except BotClient.DoesNotExist:
                # Fall back to primary key lookup
                try:
                    return BotClient.objects.get(pk=pk)
                except BotClient.DoesNotExist:
                    pass
        return super().get_object()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Telegram ID unikal ligini tekshirish
            telegram_id = serializer.validated_data.get('telegram_id')
            if BotClient.objects.filter(telegram_id=telegram_id).exists():
                return Response(
                    {'error': 'Bu Telegram ID bilan foydalanuvchi mavjud'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                BotClientSerializer(serializer.instance).data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def active_clients(self, request):
        """Faol klientlarni olish"""
        active_clients = self.get_queryset().filter(is_active=True, is_banned=False)
        page = self.paginate_queryset(active_clients)
        if page is not None:
            serializer = BotClientListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BotClientListSerializer(active_clients, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def banned_clients(self, request):
        """Bloklangan klientlarni olish"""
        banned_clients = self.get_queryset().filter(is_banned=True)
        page = self.paginate_queryset(banned_clients)
        if page is not None:
            serializer = BotClientListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BotClientListSerializer(banned_clients, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def ban(self, request, pk=None):
        """Klientni bloklash"""
        client = self.get_object()
        client.is_banned = True
        client.is_active = False
        client.save()
        serializer = BotClientSerializer(client)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unban(self, request, pk=None):
        """Klientni blokdan chiqarish"""
        client = self.get_object()
        client.is_banned = False
        client.is_active = True
        client.save()
        serializer = BotClientSerializer(client)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_rating(self, request, pk=None):
        """Klient reytingini yangilash"""
        client = self.get_object()
        rating = request.data.get('rating')

        if rating is None:
            return Response(
                {'error': 'Rating talab qilinadi'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rating = float(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'Rating 1 dan 5 gacha bo\'lishi kerak'},
                status=status.HTTP_400_BAD_REQUEST
            )

        client.rating = rating
        client.save()
        serializer = BotClientSerializer(client)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def increment_rides(self, request, pk=None):
        """Safar sonini oshirish"""
        client = self.get_object()
        client.total_rides += 1
        client.save()
        serializer = BotClientSerializer(client)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistika olish"""
        total_clients = self.get_queryset().count()
        active_clients = self.get_queryset().filter(is_active=True).count()
        banned_clients = self.get_queryset().filter(is_banned=True).count()
        total_rides = self.get_queryset().aggregate(models.Sum('total_rides'))['total_rides__sum'] or 0

        return Response({
            'total_clients': total_clients,
            'active_clients': active_clients,
            'banned_clients': banned_clients,
            'total_rides': total_rides
        })

    @action(detail=False, methods=['get'], url_path='by-telegram-id/(?P<telegram_id>[^/.]+)')
    def by_telegram_id(self, request, telegram_id=None):
        """Get client by telegram ID"""
        try:
            client = BotClient.objects.get(telegram_id=telegram_id)
            serializer = BotClientSerializer(client)
            return Response(serializer.data)
        except BotClient.DoesNotExist:
            return Response(
                {'error': 'Foydalanuvchi topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )


class BotClientPublicViewSet(viewsets.ReadOnlyModelViewSet):
    """Ommaviy API (faqat o'qish uchun)"""
    queryset = BotClient.objects.filter(is_active=True, is_banned=False)
    serializer_class = BotClientListSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['full_name', 'username']