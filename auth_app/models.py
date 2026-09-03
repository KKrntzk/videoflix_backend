from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    """Manager that keeps superusers active despite the inactive default."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Creates a superuser that is active from the start."""
        extra_fields.setdefault("is_active", True)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """User authenticating by email while keeping the username field."""

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["email"]

    def __str__(self):
        return self.email
