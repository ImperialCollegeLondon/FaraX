"""Database models for the main app."""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """A user of FaraX.

    This has no fields beyond Django's built-in user. It is in place from the first
    migration so that it can be extended later without a difficult migration.
    """
