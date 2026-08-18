import logging

from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .lgpd import delete_user_data
from .models import User
from .serializers import LoginSerializer, MeSerializer, RegisterSerializer

logger = logging.getLogger("finez")


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(MeSerializer(user).data, status=status.HTTP_201_CREATED)


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post")
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return Response(MeSerializer(user).data)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(MeSerializer(request.user).data)

    def patch(self, request):
        serializer = MeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        """Exclusão LGPD completa (seção 5): revoga consentimentos, hard delete, tombstone."""
        user_id = request.user.id
        delete_user_data(request.user)
        logout(request)
        logger.info("lgpd_deletion_completed", extra={"user_id": str(user_id)})
        return Response(status=status.HTTP_204_NO_CONTENT)
