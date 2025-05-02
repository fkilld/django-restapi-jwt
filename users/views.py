from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from .serializers import RegisterSerializer
from rest_framework.response import Response
from rest_framework import status


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class UserProfileView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        content = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        return Response(content)
