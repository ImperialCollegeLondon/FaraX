"""Database models for the main app."""

from django.contrib.auth.models import AbstractUser

ADMIN_GROUP_NAME = "Admin"


class User(AbstractUser):
    """A user of FaraX.

    This has no fields beyond Django's built-in user. It is in place from the first
    migration so that it can be extended later without a difficult migration.
    """

    @property
    def is_admin(self) -> bool:
        """Return whether this user belongs to FaraX's Admin role."""
        return self.groups.filter(name=ADMIN_GROUP_NAME).exists()
