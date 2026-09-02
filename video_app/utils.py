import subprocess
from pathlib import Path

from django.conf import settings

RESOLUTIONS = {
    "480p": "854x480",
    "720p": "1280x720",
    "1080p": "1920x1080",
}


def build_thumbnail_path(video_id):
    """Returns the temporary path where a thumbnail is generated."""
    return Path(settings.MEDIA_ROOT) / "tmp" / f"{video_id}.jpg"


def extract_thumbnail(source_path, target_path):
    """Grabs a single frame from the video and saves it as an image."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        "00:00:03",
        "-i",
        str(source_path),
        "-frames:v",
        "1",
        "-update",
        "1",
        "-q:v",
        "2",
        str(target_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def build_hls_dir(video_id, resolution):
    """Returns the directory holding one resolution's HLS files."""
    return Path(settings.MEDIA_ROOT) / "videos" / str(video_id) / resolution


def build_hls_command(source_path, target_dir, size):
    """Assembles the ffmpeg command for one HLS rendition."""
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-vf",
        f"scale={size}",
        "-c:v",
        "libx264",
        "-crf",
        "23",
        "-preset",
        "fast",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-start_number",
        "0",
        "-hls_time",
        "10",
        "-hls_list_size",
        "0",
        "-hls_segment_filename",
        str(target_dir / "%03d.ts"),
        "-f",
        "hls",
        str(target_dir / "index.m3u8"),
    ]


def convert_to_hls(source_path, video_id, resolution):
    """Transcodes a video into HLS segments for one resolution."""
    target_dir = build_hls_dir(video_id, resolution)
    target_dir.mkdir(parents=True, exist_ok=True)
    size = RESOLUTIONS[resolution].replace("x", ":")
    cmd = build_hls_command(source_path, target_dir, size)
    subprocess.run(cmd, capture_output=True, check=True)
