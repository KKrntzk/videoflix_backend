import shutil
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from video_app.models import Video

User = get_user_model()

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class StreamingViewTest(APITestCase):
    """Tests for the HLS manifest and segment endpoints."""

    @classmethod
    def tearDownClass(cls):
        """Removes the temporary media directory after all tests."""
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        """Create an active user, a video and fake HLS files."""
        self.user = User.objects.create_user(
            username="streamer@mail.de",
            email="streamer@mail.de",
            password="securepassword123",
        )
        self.user.is_active = True
        self.user.save()
        self.credentials = {
            "email": "streamer@mail.de",
            "password": "securepassword123",
        }
        self.video = Video.objects.create(
            title="Streamable", description="Test", category="drama"
        )
        self._create_hls_files()

    def _create_hls_files(self):
        """Writes a minimal manifest and segment to the temporary media root."""
        directory = Path(MEDIA_ROOT) / "videos" / str(self.video.id) / "720p"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.m3u8").write_text("#EXTM3U\n000.ts\n")
        (directory / "000.ts").write_bytes(b"fake segment data")

    def login(self):
        """Logs the test client in so the auth cookies are set."""
        return self.client.post(reverse("login"), self.credentials)

    def manifest_url(self, video_id, resolution):
        """Returns the manifest url for a video and resolution."""
        return reverse(
            "video-manifest",
            kwargs={"movie_id": video_id, "resolution": resolution},
        )

    def segment_url(self, video_id, resolution, segment):
        """Returns the segment url for a video, resolution and file."""
        return reverse(
            "video-segment",
            kwargs={
                "movie_id": video_id,
                "resolution": resolution,
                "segment": segment,
            },
        )

    def test_manifest_requires_authentication(self):
        """An anonymous manifest request is rejected with a 401."""
        response = self.client.get(self.manifest_url(self.video.id, "720p"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manifest_success(self):
        """An authenticated user receives the manifest file."""
        self.login()
        response = self.client.get(self.manifest_url(self.video.id, "720p"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manifest_content_type(self):
        """The manifest is served with the HLS content type."""
        self.login()
        response = self.client.get(self.manifest_url(self.video.id, "720p"))
        self.assertEqual(response["Content-Type"], "application/vnd.apple.mpegurl")

    def test_manifest_unknown_resolution(self):
        """An unsupported resolution returns a 404."""
        self.login()
        response = self.client.get(self.manifest_url(self.video.id, "999p"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manifest_missing_file(self):
        """A resolution that was never generated returns a 404."""
        self.login()
        response = self.client.get(self.manifest_url(self.video.id, "1080p"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manifest_unknown_video(self):
        """A video id that does not exist returns a 404."""
        self.login()
        response = self.client.get(self.manifest_url(9999, "720p"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_segment_requires_authentication(self):
        """An anonymous segment request is rejected with a 401."""
        response = self.client.get(self.segment_url(self.video.id, "720p", "000.ts"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_segment_success(self):
        """An authenticated user receives the segment file."""
        self.login()
        response = self.client.get(self.segment_url(self.video.id, "720p", "000.ts"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_segment_content_type(self):
        """The segment is served with the MPEG transport stream type."""
        self.login()
        response = self.client.get(self.segment_url(self.video.id, "720p", "000.ts"))
        self.assertEqual(response["Content-Type"], "video/MP2T")

    def test_segment_missing_file(self):
        """A segment that does not exist returns a 404."""
        self.login()
        response = self.client.get(self.segment_url(self.video.id, "720p", "999.ts"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_segment_rejects_non_ts_files(self):
        """Only .ts files may be requested through the segment endpoint."""
        self.login()
        response = self.client.get(
            self.segment_url(self.video.id, "720p", "index.m3u8")
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_segment_rejects_unknown_resolution(self):
        """An unsupported resolution is rejected before any file access."""
        self.login()
        response = self.client.get(self.segment_url(self.video.id, "999p", "000.ts"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
