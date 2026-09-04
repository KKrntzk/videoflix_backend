import django_rq
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Video
from .tasks import create_hls_rendition, create_thumbnail
from .utils import RESOLUTIONS, delete_video_files


@receiver(post_save, sender=Video)
def enqueue_video_processing(sender, instance, created, **kwargs):
    """Queues thumbnail and HLS jobs whenever a new video is uploaded."""
    if not created:
        return
    queue = django_rq.get_queue("low")
    queue.enqueue(create_thumbnail, instance.id)
    for resolution in RESOLUTIONS:
        queue.enqueue(create_hls_rendition, instance.id, resolution)


@receiver(post_delete, sender=Video)
def remove_video_files(sender, instance, **kwargs):
    """Deletes all files belonging to a video once it is removed."""
    delete_video_files(instance)
