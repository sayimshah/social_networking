from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework import (
    generics, permissions, status, viewsets, 
    authentication, exceptions, views
)
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from ..models import FriendRequest, Friendship
from .serializers import UserSerializer, FriendRequestSerializer, FriendshipSerializer
from django.contrib.auth import authenticate

User = get_user_model()


class UserSignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UserLoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email').lower()
        password = request.data.get('password')
        user = authenticate(email=email, password=password)
        if user:
            token, created = authentication.Token.objects.get_or_create(user=user)
            return Response(
                {'message': 'LogIn Successful', 'token': token.key},
                status=status.HTTP_200_OK
            )
        return Response(
            {'error': 'Invalid Credentials'},
            status=status.HTTP_400_BAD_REQUEST
        )


class UserSearchView(generics.ListAPIView):
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get('q', '').lower()
        if '@' in query:
            return User.objects.filter(email=query)
        return User.objects.filter(name__icontains=query)


class PendingFriendRequestsView(generics.ListAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            pending_requests = FriendRequest.objects.filter(receiver=self.request.user, status='pending')
            if not pending_requests.exists():
                raise exceptions.NotFound(detail="No pending friend requests found.")
            return pending_requests
        except Exception as e:
            raise e

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data,
            'message': 'Pending friend requests retrieved successfully.'
        }, status=status.HTTP_200_OK)


class FriendRequestViewSet(viewsets.ModelViewSet):
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FriendRequest.objects.filter(receiver=self.request.user)

    @action(detail=False, methods=['post'], url_path='send')
    def send_request(self, request):
        sender = request.user
        receiver_id = request.data.get('receiver_id')
        try:
            receiver = User.objects.get(id=receiver_id)
        except ObjectDoesNotExist:
            return Response(
                {'error': 'Receiver not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if FriendRequest.objects.filter(sender=sender, receiver=receiver).exists():
            return Response(
                {'error': 'Friend request already sent'},
                status=status.HTTP_400_BAD_REQUEST
            )

        one_minute_ago = timezone.now() - timedelta(minutes=1)
        requests_in_last_minute = FriendRequest.objects.filter(sender=sender, timestamp__gte=one_minute_ago).count()
        if requests_in_last_minute >= 3:
            return Response(
                {'error': 'You cannot send more than 3 friend requests within a minute'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        friend_request = FriendRequest.objects.create(sender=sender, receiver=receiver)
        return Response(
            FriendRequestSerializer(friend_request).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='accept')
    def accept_request(self, request, pk=None):
        try:
            friend_request = self.get_object()
        except ObjectDoesNotExist:
            return Response(
                {'error': 'Friend request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if friend_request.receiver != request.user:
            return Response(
                {'error': 'You are not authorized to accept this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        existing_friendship = Friendship.objects.filter(
            Q(user1=friend_request.sender, user2=friend_request.receiver) |
            Q(user1=friend_request.receiver, user2=friend_request.sender)
        ).first()
        if existing_friendship:
            return Response(
                {'error': 'Friendship already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        friend_request.status = 'accepted'
        friend_request.save()

        Friendship.objects.create(user1=friend_request.sender, user2=friend_request.receiver)

        return Response(
            {'status': 'Friend request accepted'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_request(self, request, pk=None):
        try:
            friend_request = self.get_object()
        except ObjectDoesNotExist:
            return Response(
                {'error': 'Friend request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if friend_request.receiver != request.user:
            return Response(
                {'error': 'You are not authorized to reject this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        if friend_request.status == 'rejected':
            return Response(
                {'error': 'Friend request has already been rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        friend_request.status = 'rejected'
        friend_request.save()
        return Response(
            {'status': 'Friend request rejected'},
            status=status.HTTP_200_OK
        )


class FriendListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        friends_as_receiver = FriendRequest.objects.filter(receiver=user, status='accepted').values_list('sender', flat=True)
        friends_as_sender = FriendRequest.objects.filter(sender=user, status='accepted').values_list('receiver', flat=True)
        friends_ids = set(friends_as_receiver).union(set(friends_as_sender))
        return User.objects.filter(id__in=friends_ids)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data,
            'message': 'Friends list retrieved successfully.'
        }, status=status.HTTP_200_OK)
