import django_rq
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..tasks import send_activation_email
from ..utils import build_activation_link
from .serializers import RegistrationSerializer


class RegistrationView(APIView):
    """Creates a new inactive user and queues the activation email."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        self._enqueue_activation_email(user)
        return Response(
            {"user": {"id": user.id, "email": user.email}},
            status=status.HTTP_201_CREATED,
        )

    def _enqueue_activation_email(self, user):
        """Queues the activation email for background delivery."""
        link = build_activation_link(user, settings.FRONTEND_URL)
        django_rq.get_queue("default").enqueue(send_activation_email, user.email, link)
