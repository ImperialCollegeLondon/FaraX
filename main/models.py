"""Database models for the main app."""

import json
from collections.abc import Iterable

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.base import ModelBase


class User(AbstractUser):
    """A user of FaraX.

    This has no fields beyond Django's built-in user. It is in place from the first
    migration so that it can be extended later without a difficult migration.
    """


class RegisteredSchema(models.Model):
    """A schema registered by an administrator for use elsewhere in FaraX.

    Only the parsed JSON definition is stored, not the uploaded file. Names are
    unique and case-sensitive, so `Co` and `CO` can both be registered.

    The definition cannot change once registered; only the name can be corrected.
    Bulk updates and direct SQL are not checked.
    """

    name = models.CharField(max_length=255, unique=True)
    definition = models.JSONField()

    def __str__(self) -> str:
        """Return the display name."""
        return self.name

    def save(
        self,
        *,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        """Save the registration, refusing any change to the definition.

        Definitions are compared as canonical JSON, so `1`, `1.0` and `true` count
        as different. Updates never write the definition column. After an insert the
        definition is reloaded so it matches what the database stored.

        Raises:
            ValidationError: If the definition differs from the stored one.
        """
        stored: object = None
        if self.pk is not None:
            try:
                stored = (
                    RegisteredSchema.objects.using(using or self._state.db)
                    .get(pk=self.pk)
                    .definition
                )
            except RegisteredSchema.DoesNotExist:
                pass
            else:
                if _canonical(stored) != _canonical(self.definition):
                    raise ValidationError(
                        "A registered definition cannot be changed. Register a new "
                        "schema instead.",
                        code="immutable",
                    )
                allowed = {
                    field.name
                    for field in self._meta.concrete_fields
                    if not field.primary_key and field.name != "definition"
                }
                update_fields = (
                    allowed
                    if update_fields is None
                    else allowed.intersection(update_fields)
                )
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        if not stored:
            # The database may normalise the JSON, e.g. 1e20 to an integer.
            self.refresh_from_db(fields=["definition"], using=using)


def _canonical(value: object) -> str:
    """Return JSON text that is equal only for identical JSON values."""
    return json.dumps(value, sort_keys=True)
