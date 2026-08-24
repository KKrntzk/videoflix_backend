import django_rq
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..tasks import send_activation_email
from ..tokens import account_activation_token
from ..utils import build_activation_link, get_user_from_uidb64
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


class ActivationView(APIView):
    """Activates a user account via the emailed uid and token."""

    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        user = get_user_from_uidb64(uidb64)
        if user is None or not account_activation_token.check_token(user, token):
            return Response(
                {"message": "Activation failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = True
        user.save()
        return Response({"message": "Account successfully activated."})
