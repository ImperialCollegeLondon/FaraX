"""Database models for the main app."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """A user of FaraX.

    This has no fields beyond Django's built-in user. It is in place from the first
    migration so that it can be extended later without a difficult migration.
    """


class RegisteredSchema(models.Model):
    """A schema registered by an administrator for use elsewhere in FaraX.

    Only the parsed JSON definition is stored, not the uploaded file. Names are
    unique and case-sensitive, so `Co` and `CO` can both be registered.
    """

    name = models.CharField(max_length=255, unique=True)
    definition = models.JSONField()

    def __str__(self) -> str:
        """Return the display name."""
        return self.name
