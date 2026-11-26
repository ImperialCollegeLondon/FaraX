"""Grant the Admin group permissions to manage registered schemas."""

from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps

ADMIN_GROUP_NAME = "Admin"
SCHEMA_PERMISSION_NAMES = {
    "add_registeredschema": "Can add registered schema",
    "change_registeredschema": "Can change registered schema",
    "delete_registeredschema": "Can delete registered schema",
    "view_registeredschema": "Can view registered schema",
}


def add_schema_permissions(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    """Grant the Admin group all registered schema permissions."""
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    database = schema_editor.connection.alias

    content_type, _ = ContentType.objects.using(database).get_or_create(
        app_label="main", model="registeredschema"
    )
    permissions = [
        Permission.objects.using(database).get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": name},
        )[0]
        for codename, name in SCHEMA_PERMISSION_NAMES.items()
    ]
    group, _ = Group.objects.using(database).get_or_create(name=ADMIN_GROUP_NAME)
    group.permissions.add(*permissions)


def remove_schema_permissions(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    """Remove the registered schema permissions from the Admin group."""
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    database = schema_editor.connection.alias

    permissions = Permission.objects.using(database).filter(
        content_type__app_label="main",
        codename__in=SCHEMA_PERMISSION_NAMES,
    )
    for group in Group.objects.using(database).filter(name=ADMIN_GROUP_NAME):
        group.permissions.remove(*permissions)


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0003_registeredschema"),
    ]

    operations = [
        migrations.RunPython(add_schema_permissions, remove_schema_permissions),
    ]
