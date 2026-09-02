from rest_framework import serializers

from ..models import Video


class VideoListSerializer(serializers.ModelSerializer):
    """Serializes video metadata for the dashboard listing."""

    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            "id",
            "created_at",
            "title",
            "description",
            "thumbnail_url",
            "category",
        ]

    def get_thumbnail_url(self, obj):
        """Returns the absolute URL of the video's thumbnail."""
        if not obj.thumbnail:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.thumbnail.url)
