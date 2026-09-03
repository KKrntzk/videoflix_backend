from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """Reads the JWT access token from an HttpOnly cookie."""

    def authenticate(self, request):
        """Returns the user for a valid cookie token, or None."""
        raw_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE"])
        if raw_token is None:
            return None
        return self._authenticate_token(raw_token)

    def _authenticate_token(self, raw_token):
        """Validates the token and returns None if it is unusable."""
        try:
            validated_token = self.get_validated_token(raw_token)
        except (InvalidToken, TokenError):
            return None
        return self.get_user(validated_token), validated_token
