import django_rq
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Video
from .tasks import create_hls_rendition, create_thumbnail
from .utils import RESOLUTIONS


@receiver(post_save, sender=Video)
def enqueue_video_processing(sender, instance, created, **kwargs):
    """Queues thumbnail and HLS jobs whenever a new video is uploaded."""
    if not created:
        return
    queue = django_rq.get_queue("default")
    queue.enqueue(create_thumbnail, instance.id)
    for resolution in RESOLUTIONS:
        queue.enqueue(create_hls_rendition, instance.id, resolution)
