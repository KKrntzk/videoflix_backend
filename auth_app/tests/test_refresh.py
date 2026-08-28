from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class LogoutRefreshTest(APITestCase):
    """Tests for POST /api/logout/ and POST /api/token/refresh/."""

    def setUp(self):
        """Create an active user and store the relevant urls."""
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.refresh_url = reverse("token_refresh")
        self.user = User.objects.create_user(
            username="active@mail.de",
            email="active@mail.de",
            password="securepassword123",
        )
        self.user.is_active = True
        self.user.save()
        self.credentials = {
            "email": "active@mail.de",
            "password": "securepassword123",
        }

    def login(self):
        """Logs the test client in so the auth cookies are set."""
        return self.client.post(self.login_url, self.credentials)

    def test_logout_success(self):
        """An authenticated user can log out."""
        self.login()
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_clears_cookies(self):
        """Logging out empties both auth cookies."""
        self.login()
        response = self.client.post(self.logout_url)
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"].value, "")

    def test_logout_without_cookies(self):
        """Logging out without a refresh cookie is rejected with a 400."""
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_with_invalid_token(self):
        """An invalid refresh cookie still clears the session cleanly."""
        self.client.cookies["refresh_token"] = "invalid"
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_blacklists_refresh_token(self):
        """The refresh token cannot be used again after logging out."""
        self.login()
        refresh_token = self.client.cookies["refresh_token"].value
        self.client.post(self.logout_url)
        self.client.cookies["refresh_token"] = refresh_token
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_success(self):
        """A valid refresh cookie returns a new access token."""
        self.login()
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_sets_new_access_cookie(self):
        """The refreshed access token is stored as a cookie."""
        self.login()
        response = self.client.post(self.refresh_url)
        self.assertNotEqual(response.cookies["access_token"].value, "")

    def test_refresh_without_cookie(self):
        """A missing refresh cookie is rejected with a 400."""
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_with_invalid_token(self):
        """An invalid refresh cookie is rejected with a 401."""
        self.client.cookies["refresh_token"] = "invalid"
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
