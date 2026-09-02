from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from ..models import Video
from .serializers import VideoListSerializer


class VideoListView(ListAPIView):
    """Returns all available videos, newest first."""

    queryset = Video.objects.all()
    serializer_class = VideoListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
