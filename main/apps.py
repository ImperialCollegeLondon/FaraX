"""App configuration for the main app."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

if TYPE_CHECKING:
    from .models import User


class MainConfig(AppConfig):
    """Configuration for the main app."""

    name = "main"

    def ready(self) -> None:
        """Assign the Admin role to newly-created superusers."""
        post_save.connect(
            assign_admin_role,
            sender=get_user_model(),
            dispatch_uid="main.assign_admin_role",
        )


def assign_admin_role(
    sender: type[User], instance: User, created: bool, **kwargs: object
) -> None:
    """Assign the Admin role to a newly-created superuser."""
    from django.contrib.auth.models import Group

    from .models import ADMIN_GROUP_NAME

    if created and instance.is_superuser:
        admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP_NAME)
        instance.groups.add(admin_group)
