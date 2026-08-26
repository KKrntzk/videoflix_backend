from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class LoginViewTest(APITestCase):
    """Tests for POST /api/login/."""

    def setUp(self):
        """Create an active user and provide the login url and payload."""
        self.url = reverse("login")
        self.user = User.objects.create_user(
            username="loginuser@mail.de",
            email="loginuser@mail.de",
            password="securepassword123",
        )
        self.user.is_active = True
        self.user.save()
        self.valid_payload = {
            "email": "loginuser@mail.de",
            "password": "securepassword123",
        }

    def test_login_success(self):
        """Valid credentials return 200 with a detail message."""
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Login successful")

    def test_login_returns_user_data(self):
        """The response contains the user's id and email."""
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.data["user"]["id"], self.user.id)
        self.assertEqual(response.data["user"]["username"], "loginuser@mail.de")

    def test_login_sets_cookies(self):
        """A successful login sets access and refresh token cookies."""
        response = self.client.post(self.url, self.valid_payload)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_login_cookies_are_httponly(self):
        """Both token cookies are flagged as HttpOnly."""
        response = self.client.post(self.url, self.valid_payload)
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    def test_login_tokens_not_in_body(self):
        """The raw tokens are never exposed in the response body."""
        response = self.client.post(self.url, self.valid_payload)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_login_wrong_password(self):
        """A wrong password is rejected with a 400."""
        payload = {"email": "loginuser@mail.de", "password": "wrongpassword"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        """An email that does not exist is rejected with a 400."""
        payload = {"email": "ghost@mail.de", "password": "securepassword123"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user(self):
        """A user who has not confirmed their email cannot log in."""
        User.objects.create_user(
            username="pending@mail.de",
            email="pending@mail.de",
            password="securepassword123",
        )
        payload = {"email": "pending@mail.de", "password": "securepassword123"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_errors_are_identical(self):
        """Wrong password and unknown email produce the same message."""
        wrong = self.client.post(
            self.url, {"email": "loginuser@mail.de", "password": "nope"}
        )
        unknown = self.client.post(
            self.url, {"email": "ghost@mail.de", "password": "securepassword123"}
        )
        self.assertEqual(str(wrong.data), str(unknown.data))

    def test_login_missing_password(self):
        """A request without a password is rejected with a 400."""
        response = self.client.post(self.url, {"email": "loginuser@mail.de"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_email(self):
        """A request without an email is rejected with a 400."""
        response = self.client.post(self.url, {"password": "securepassword123"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_empty_payload(self):
        """An empty request body is rejected with a 400."""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_no_cookies_on_failure(self):
        """A failed login does not set any auth cookies."""
        payload = {"email": "loginuser@mail.de", "password": "wrongpassword"}
        response = self.client.post(self.url, payload)
        self.assertNotIn("access_token", response.cookies)
        self.assertNotIn("refresh_token", response.cookies)
