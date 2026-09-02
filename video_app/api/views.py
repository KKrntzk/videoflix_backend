from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from ..models import Video
from .serializers import VideoListSerializer

from django.http import FileResponse, Http404
from rest_framework.views import APIView

from ..utils import RESOLUTIONS, build_manifest_path, build_segment_path


class VideoListView(ListAPIView):
    """Returns all available videos, newest first."""

    queryset = Video.objects.all()
    serializer_class = VideoListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class HLSManifestView(APIView):
    """Serves the HLS manifest for one video and resolution."""

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        if resolution not in RESOLUTIONS:
            raise Http404
        path = build_manifest_path(movie_id, resolution)
        if not path.exists():
            raise Http404
        return FileResponse(
            open(path, "rb"), content_type="application/vnd.apple.mpegurl"
        )


class HLSSegmentView(APIView):
    """Serves a single HLS segment for one video and resolution."""

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        if resolution not in RESOLUTIONS or not segment.endswith(".ts"):
            raise Http404
        path = build_segment_path(movie_id, resolution, segment)
        if not path.exists():
            raise Http404
        return FileResponse(open(path, "rb"), content_type="video/MP2T")
