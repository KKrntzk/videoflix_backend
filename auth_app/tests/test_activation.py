from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.tokens import account_activation_token

User = get_user_model()


class ActivationViewTest(APITestCase):
    """Tests for GET /api/activate/<uidb64>/<token>/."""

    def setUp(self):
        """Create an inactive user and build a valid activation link."""
        self.user = User.objects.create_user(
            username="pending@mail.de",
            email="pending@mail.de",
            password="securepassword123",
        )
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = account_activation_token.make_token(self.user)

    def build_url(self, uidb64, token):
        """Returns the activation url for the given uid and token."""
        return reverse("activate", kwargs={"uidb64": uidb64, "token": token})

    def test_activation_success(self):
        """A valid link activates the account and returns 200."""
        response = self.client.get(self.build_url(self.uidb64, self.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_activation_sets_user_active(self):
        """The user is marked as active in the database."""
        self.client.get(self.build_url(self.uidb64, self.token))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_activation_token_is_single_use(self):
        """A token stops working once the account has been activated."""
        self.client.get(self.build_url(self.uidb64, self.token))
        response = self.client.get(self.build_url(self.uidb64, self.token))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activation_invalid_token(self):
        """A tampered token is rejected with a 400."""
        response = self.client.get(self.build_url(self.uidb64, "invalid-token"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activation_invalid_uid(self):
        """A malformed uid is rejected with a 400."""
        response = self.client.get(self.build_url("XXXX", self.token))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activation_unknown_user(self):
        """A uid of a non-existing user is rejected with a 400."""
        uidb64 = urlsafe_base64_encode(force_bytes(9999))
        response = self.client.get(self.build_url(uidb64, self.token))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activation_keeps_user_inactive_on_failure(self):
        """A failed activation does not change the user's status."""
        self.client.get(self.build_url(self.uidb64, "invalid-token"))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
