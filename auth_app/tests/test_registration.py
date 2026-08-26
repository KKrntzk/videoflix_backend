from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationViewTest(APITestCase):
    """Tests for POST /api/register/."""

    def setUp(self):
        """Provide the registration url and a valid payload."""
        self.url = reverse("register")
        self.valid_payload = {
            "email": "newuser@mail.de",
            "password": "securepassword123",
            "confirmed_password": "securepassword123",
        }

    def test_registration_success(self):
        """Valid data creates a user and returns 201."""
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="newuser@mail.de").exists())

    def test_registration_returns_user_data(self):
        """The response contains the new user's id and email."""
        response = self.client.post(self.url, self.valid_payload)
        self.assertIn("id", response.data["user"])
        self.assertEqual(response.data["user"]["email"], "newuser@mail.de")

    def test_registration_creates_inactive_user(self):
        """A new user must confirm their email before logging in."""
        self.client.post(self.url, self.valid_payload)
        user = User.objects.get(email="newuser@mail.de")
        self.assertFalse(user.is_active)

    def test_registration_sets_username_to_email(self):
        """The username field is filled with the email address."""
        self.client.post(self.url, self.valid_payload)
        user = User.objects.get(email="newuser@mail.de")
        self.assertEqual(user.username, "newuser@mail.de")

    def test_registration_hashes_password(self):
        """The raw password is never stored in the database."""
        self.client.post(self.url, self.valid_payload)
        user = User.objects.get(email="newuser@mail.de")
        self.assertNotEqual(user.password, "securepassword123")

    def test_registration_password_not_in_response(self):
        """The password is never echoed back to the client."""
        response = self.client.post(self.url, self.valid_payload)
        self.assertNotIn("password", str(response.data))

    def test_registration_duplicate_email(self):
        """An already registered email is rejected with a 400."""
        self.client.post(self.url, self.valid_payload)
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email_stays_generic(self):
        """The duplicate error must not reveal that the account exists."""
        self.client.post(self.url, self.valid_payload)
        response = self.client.post(self.url, self.valid_payload)
        self.assertNotIn("already exists", str(response.data).lower())

    def test_registration_password_mismatch(self):
        """Mismatching passwords are rejected with a 400."""
        payload = dict(self.valid_payload, confirmed_password="different")
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_invalid_email(self):
        """A malformed email address is rejected with a 400."""
        payload = dict(self.valid_payload, email="notanemail")
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_missing_password(self):
        """A request without a password is rejected with a 400."""
        response = self.client.post(self.url, {"email": "x@mail.de"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_empty_payload(self):
        """An empty request body is rejected with a 400."""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_no_user_on_failure(self):
        """A failed registration does not create a database entry."""
        payload = dict(self.valid_payload, confirmed_password="different")
        self.client.post(self.url, payload)
        self.assertFalse(User.objects.filter(email="newuser@mail.de").exists())
