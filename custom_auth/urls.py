from django.urls import path
from .views import LoginView, RefreshTokenView, ProfileView, UserListView, UserDetailView

urlpatterns = [
    path('auth/login', LoginView.as_view(), name='login'),
    path('auth/refresh-token', RefreshTokenView.as_view(), name='refresh-token'),
    path('users/me', ProfileView.as_view(), name='profile'),
    path('users', UserListView.as_view(), name='user-list'),
    path('users/<uuid:pk>', UserDetailView.as_view(), name='user-detail'),
]
