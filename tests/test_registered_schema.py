"""Tests for the RegisteredSchema model."""

import pytest
from django.core.exceptions import ValidationError

from main.models import RegisteredSchema


@pytest.mark.parametrize(
    ("stored", "changed"),
    [({"a": 1}, {"a": 2}), ({"a": 1}, {"a": True}), ({"a": 1}, {"a": 1.0})],
)
def test_save_refuses_changed_definition(db, stored, changed):
    """An ordinary save with a different definition is refused and writes nothing."""
    schema = RegisteredSchema.objects.create(name="Co", definition=stored)
    schema.name = "Renamed"
    schema.definition = changed

    with pytest.raises(ValidationError) as excinfo:
        schema.save()

    assert excinfo.value.code == "immutable"
    stored_row = RegisteredSchema.objects.get()
    assert stored_row.name == "Co"
    assert stored_row.definition == stored
    assert repr(stored_row.definition) == repr(stored)


def test_save_allows_name_change(db):
    """A name-only change saves and leaves the definition alone."""
    schema = RegisteredSchema.objects.create(name="Co", definition={"b": 1, "a": 2})
    schema.name = "Cobalt"
    schema.save()

    stored_row = RegisteredSchema.objects.get()
    assert stored_row.name == "Cobalt"
    assert stored_row.definition == {"a": 2, "b": 1}


def test_save_refuses_new_instance_over_existing_pk(db):
    """A fresh instance with an existing pk cannot overwrite the stored definition."""
    original = RegisteredSchema.objects.create(
        name="original", definition={"type": "string"}
    )

    with pytest.raises(ValidationError) as excinfo:
        RegisteredSchema(
            pk=original.pk, name="replacement", definition={"type": "number"}
        ).save()

    assert excinfo.value.code == "immutable"
    stored_row = RegisteredSchema.objects.get()
    assert stored_row.name == "original"
    assert stored_row.definition == {"type": "string"}


def test_rename_after_create_with_normalised_number(db):
    """A rename after create works when the database normalises the definition.

    PostgreSQL stores `1e20` as `100000000000000000000`; this only fails there and
    passes on SQLite.
    """
    schema = RegisteredSchema.objects.create(name="Co", definition={"maximum": 1e20})
    schema.name = "Cobalt"
    schema.save()

    assert RegisteredSchema.objects.get().name == "Cobalt"
