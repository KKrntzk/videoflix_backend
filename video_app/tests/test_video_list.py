import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from video_app.models import Video

User = get_user_model()

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class VideoListViewTest(APITestCase):
    """Tests for GET /api/video/."""

    @classmethod
    def tearDownClass(cls):
        """Removes the temporary media directory after all tests."""
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        """Create an active user and two videos to list."""
        self.url = reverse("video-list")
        self.user = User.objects.create_user(
            username="viewer@mail.de",
            email="viewer@mail.de",
            password="securepassword123",
        )
        self.user.is_active = True
        self.user.save()
        self.credentials = {
            "email": "viewer@mail.de",
            "password": "securepassword123",
        }
        self.older = Video.objects.create(
            title="Older Movie", description="First", category="drama"
        )
        self.newer = Video.objects.create(
            title="Newer Movie", description="Second", category="comedy"
        )

    def login(self):
        """Logs the test client in so the auth cookies are set."""
        return self.client.post(reverse("login"), self.credentials)

    def test_list_requires_authentication(self):
        """An anonymous request is rejected with a 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_videos(self):
        """An authenticated user receives all available videos."""
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_is_not_paginated(self):
        """The response is a plain list, not a paginated object."""
        self.login()
        response = self.client.get(self.url)
        self.assertIsInstance(response.data, list)

    def test_list_contains_expected_fields(self):
        """Each entry exposes exactly the documented fields."""
        self.login()
        response = self.client.get(self.url)
        expected = {
            "id",
            "created_at",
            "title",
            "description",
            "thumbnail_url",
            "category",
        }
        self.assertEqual(set(response.data[0].keys()), expected)

    def test_list_is_ordered_newest_first(self):
        """Videos are sorted by creation date descending."""
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.data[0]["id"], self.newer.id)

    def test_list_thumbnail_url_is_none_without_image(self):
        """A video without a thumbnail returns null instead of a broken url."""
        self.login()
        response = self.client.get(self.url)
        self.assertIsNone(response.data[0]["thumbnail_url"])

    def test_list_is_empty_without_videos(self):
        """An empty library returns an empty list, not an error."""
        Video.objects.all().delete()
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
