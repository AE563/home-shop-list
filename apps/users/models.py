from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model. All users share one common shop list."""

    pass
