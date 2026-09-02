from django.db import models


class Video(models.Model):
    """A video available for streaming, stored in multiple resolutions."""

    CATEGORY_CHOICES = [
        ("drama", "Drama"),
        ("romance", "Romance"),
        ("comedy", "Comedy"),
        ("documentary", "Documentary"),
        ("action", "Action"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    video_file = models.FileField(upload_to="videos/originals/")
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
