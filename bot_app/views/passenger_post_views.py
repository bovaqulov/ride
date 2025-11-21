# views/passenger_post_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from ..filters.passenger_post_filter import PassengerPostFilter
from ..models import PassengerPost, TravelStatus
from ..serializers.passenger_post import (
    PassengerPostSerializer,
    PassengerPostCreateSerializer,
    PassengerPostUpdateSerializer,
    PassengerPostListSerializer
)


class PassengerPostViewSet(viewsets.ModelViewSet):
    queryset = PassengerPost.objects.all()
    filterset_class = PassengerPostFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user', 'status']
    search_fields = ['from_location', 'to_location']
    ordering_fields = ['price', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return PassengerPostCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PassengerPostUpdateSerializer
        elif self.action == 'list':
            return PassengerPostListSerializer
        return PassengerPostSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return full object after creation
        full_serializer = PassengerPostSerializer(instance)
        return Response(full_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Custom action to update post status"""
        post = self.get_object()
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

        post.status = new_status
        post.save()

        serializer = self.get_serializer(post)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Get posts by specific user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        posts = PassengerPost.objects.filter(user=user_id)
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search_routes(self, request):
        """Search for posts by from and to locations"""
        from_loc = request.query_params.get('from')
        to_loc = request.query_params.get('to')

        queryset = self.filter_queryset(self.get_queryset())

        if from_loc:
            queryset = queryset.filter(from_location__icontains=from_loc)
        if to_loc:
            queryset = queryset.filter(to_location__icontains=to_loc)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active_posts(self, request):
        """Get all active posts (CREATED status)"""
        queryset = self.filter_queryset(
            self.get_queryset().filter(status=TravelStatus.CREATED)
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def price_range(self, request):
        """Get posts within price range"""
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')

        queryset = self.filter_queryset(self.get_queryset())

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)