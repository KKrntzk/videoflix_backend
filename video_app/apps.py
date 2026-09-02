from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    """App configuration that wires up the video signals."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "video_app"

    def ready(self):
        import video_app.signals
