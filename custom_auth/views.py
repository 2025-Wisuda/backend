from rest_framework import generics, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import ProfileSerializer, UserListSerializer, UserDetailSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_api_key.permissions import HasAPIKey

User = get_user_model()

class LoginView(TokenObtainPairView):
    permission_classes = [HasAPIKey]

class RefreshTokenView(TokenRefreshView):
    permission_classes = [HasAPIKey]

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['groups__name']

class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    lookup_field = 'pk'
