from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class PasswordResetRequestTest(APITestCase):
    """Tests for POST /api/password_reset/."""

    def setUp(self):
        """Create an active user and store the reset url."""
        self.url = reverse("password_reset")
        self.user = User.objects.create_user(
            username="reset@mail.de",
            email="reset@mail.de",
            password="securepassword123",
        )
        self.user.is_active = True
        self.user.save()

    def test_reset_request_success(self):
        """A known email returns 200 with a confirmation message."""
        response = self.client.post(self.url, {"email": "reset@mail.de"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

    def test_reset_request_unknown_email(self):
        """An unknown email also returns 200 to prevent enumeration."""
        response = self.client.post(self.url, {"email": "ghost@mail.de"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_responses_are_identical(self):
        """Known and unknown emails produce the exact same response."""
        known = self.client.post(self.url, {"email": "reset@mail.de"})
        unknown = self.client.post(self.url, {"email": "ghost@mail.de"})
        self.assertEqual(str(known.data), str(unknown.data))

    def test_reset_request_invalid_email(self):
        """A malformed email is rejected with a 400."""
        response = self.client.post(self.url, {"email": "notanemail"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_request_empty_payload(self):
        """An empty request body is rejected with a 400."""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordConfirmTest(APITestCase):
    """Tests for POST /api/password_confirm/<uidb64>/<token>/."""

    def setUp(self):
        """Create an active user and build a valid reset link."""
        self.user = User.objects.create_user(
            username="confirm@mail.de",
            email="confirm@mail.de",
            password="oldpassword123",
        )
        self.user.is_active = True
        self.user.save()
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)
        self.valid_payload = {
            "new_password": "brandnewpassword456",
            "confirm_password": "brandnewpassword456",
        }

    def build_url(self, uidb64, token):
        """Returns the confirm url for the given uid and token."""
        return reverse("password_confirm", kwargs={"uidb64": uidb64, "token": token})

    def test_confirm_success(self):
        """A valid link and matching passwords return 200."""
        url = self.build_url(self.uidb64, self.token)
        response = self.client.post(url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_confirm_changes_password(self):
        """The new password is stored on the user."""
        url = self.build_url(self.uidb64, self.token)
        self.client.post(url, self.valid_payload)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("brandnewpassword456"))

    def test_confirm_invalidates_old_password(self):
        """The previous password no longer works after the reset."""
        url = self.build_url(self.uidb64, self.token)
        self.client.post(url, self.valid_payload)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("oldpassword123"))

    def test_confirm_token_is_single_use(self):
        """The token stops working once the password has changed."""
        url = self.build_url(self.uidb64, self.token)
        self.client.post(url, self.valid_payload)
        response = self.client.post(url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_password_mismatch(self):
        """Mismatching passwords are rejected with a 400."""
        url = self.build_url(self.uidb64, self.token)
        payload = dict(self.valid_payload, confirm_password="different456")
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_weak_password(self):
        """A password failing Django's validators is rejected."""
        url = self.build_url(self.uidb64, self.token)
        payload = {"new_password": "123", "confirm_password": "123"}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_invalid_token(self):
        """A tampered token is rejected with a 400."""
        url = self.build_url(self.uidb64, "invalid-token")
        response = self.client.post(url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_invalid_uid(self):
        """A malformed uid is rejected with a 400."""
        url = self.build_url("XXXX", self.token)
        response = self.client.post(url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_keeps_password_on_failure(self):
        """A failed reset leaves the original password untouched."""
        url = self.build_url(self.uidb64, "invalid-token")
        self.client.post(url, self.valid_payload)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("oldpassword123"))
