from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .tokens import account_activation_token


def build_activation_link(user, base_url):
    """Builds the frontend activation link for a given user."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    return f"{base_url}/pages/auth/activate.html?uid={uid}&token={token}"


def get_user_from_uidb64(uidb64):
    """Returns the user for a base64 encoded id, or None if invalid."""
    try:
        user_id = urlsafe_base64_decode(uidb64).decode()
        return get_user_model().objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        return None


def set_auth_cookie(response, name, value):
    """Attaches a single HttpOnly JWT cookie to the response."""
    response.set_cookie(
        key=name,
        value=value,
        httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
        secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
        samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
    )
    return response


def build_password_reset_link(user, base_url):
    """Builds the frontend password reset link for a given user."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{base_url}/pages/auth/confirm_password.html?uid={uid}&token={token}"
