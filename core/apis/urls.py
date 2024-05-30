from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PendingFriendRequestsView, UserSignupView, UserLoginView, UserSearchView, FriendRequestViewSet, FriendListView

router = DefaultRouter()
router.register(r'friend-requests', FriendRequestViewSet, basename='friend-requests')

urlpatterns = [
    path('signup/', UserSignupView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('search/', UserSearchView.as_view(), name='search'),
    path('friends/', FriendListView.as_view(), name='friends'),
    path('pending-requests/', PendingFriendRequestsView.as_view(), name='pending-friend-requests'),
    path('', include(router.urls)),
]
