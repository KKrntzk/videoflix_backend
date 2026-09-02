from django.core.files import File

from .models import Video
from .utils import build_thumbnail_path, convert_to_hls, extract_thumbnail


def create_thumbnail(video_id):
    """Extracts a thumbnail and attaches it to the video record."""
    video = Video.objects.get(pk=video_id)
    target_path = build_thumbnail_path(video_id)
    extract_thumbnail(video.video_file.path, target_path)
    _attach_thumbnail(video, target_path)


def _attach_thumbnail(video, target_path):
    """Saves the generated image on the video's thumbnail field."""
    with open(target_path, "rb") as image:
        video.thumbnail.save(target_path.name, File(image), save=True)
    target_path.unlink(missing_ok=True)


def create_hls_rendition(video_id, resolution):
    """Transcodes one video into HLS segments for a single resolution."""
    video = Video.objects.get(pk=video_id)
    convert_to_hls(video.video_file.path, video_id, resolution)
