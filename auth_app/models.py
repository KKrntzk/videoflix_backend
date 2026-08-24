from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    """Manager that keeps superusers active despite the inactive default."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_active", True)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """User authenticating by email while keeping the username field."""

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
