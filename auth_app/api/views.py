import django_rq
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from ..tasks import send_activation_email, send_password_reset_email
from ..tokens import account_activation_token
from ..utils import (
    build_activation_link,
    build_password_reset_link,
    get_user_from_uidb64,
    set_auth_cookie,
)
from .serializers import (
    LoginSerializer,
    PasswordConfirmSerializer,
    PasswordResetSerializer,
    RegistrationSerializer,
)

User = get_user_model()


class RegistrationView(APIView):
    """Creates a new inactive user and queues the activation email."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = self._enqueue_activation_email(user)
        return Response(
            {
                "user": {"id": user.id, "email": user.email},
                "token": token,
            },
            status=status.HTTP_201_CREATED,
        )

    def _enqueue_activation_email(self, user):
        """Queues the activation email and returns the activation token."""
        link = build_activation_link(user, settings.FRONTEND_URL)
        django_rq.get_queue("high").enqueue(send_activation_email, user.email, link)
        return account_activation_token.make_token(user)


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


class LoginView(APIView):
    """Authenticates a user and stores JWTs in HttpOnly cookies."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        response = Response(
            {
                "detail": "Login successful",
                "user": {"id": user.id, "username": user.email},
            }
        )
        return self._attach_tokens(response, user)

    def _attach_tokens(self, response, user):
        """Adds access and refresh cookies to the response."""
        refresh = RefreshToken.for_user(user)
        set_auth_cookie(response, "access_token", str(refresh.access_token))
        set_auth_cookie(response, "refresh_token", str(refresh))
        return response


class LogoutView(APIView):
    """Blacklists the refresh token and clears the auth cookies."""

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response(
                {"detail": "Refresh token not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self._blacklist_and_clear(refresh_token)

    def _blacklist_and_clear(self, refresh_token):
        """Invalidates the token and removes both auth cookies."""
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            pass
        response = Response(
            {
                "detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."
            }
        )
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


class CookieTokenRefreshView(APIView):
    """Issues a new access token based on the refresh cookie."""

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response(
                {"detail": "Refresh token not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self._refresh(refresh_token)

    def _refresh(self, refresh_token):
        """Validates the refresh token and returns a new access cookie."""
        try:
            access = str(RefreshToken(refresh_token).access_token)
        except TokenError:
            return Response(
                {"detail": "Refresh token invalid."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        response = Response({"detail": "Token refreshed", "access": access})
        return set_auth_cookie(response, "access_token", access)


class PasswordResetView(APIView):
    """Sends a reset link without revealing whether the account exists."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._enqueue_reset_email(serializer.validated_data["email"])
        return Response({"detail": "An email has been sent to reset your password."})

    def _enqueue_reset_email(self, email):
        """Queues the reset email only if the account exists."""
        user = User.objects.filter(email=email).first()
        if user is None:
            return
        link = build_password_reset_link(user, settings.FRONTEND_URL)
        django_rq.get_queue("high").enqueue(send_password_reset_email, email, link)


class PasswordConfirmView(APIView):
    """Sets a new password after validating the emailed token."""

    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        serializer = PasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_user_from_uidb64(uidb64)
        if user is None or not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired link."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"detail": "Your Password has been successfully reset."})
