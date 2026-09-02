from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("django-rq/", include("django_rq.urls")),
    path("api/", include("auth_app.api.urls")),
    path("api/", include("video_app.api.urls")),
]
