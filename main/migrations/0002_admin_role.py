"""Create FaraX's Admin role and assign it to existing superusers."""

from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db import migrations
from django.db.migrations.state import StateApps

ADMIN_GROUP_NAME = "Admin"


def create_admin_group(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    """Create the Admin group and assign it to existing superusers."""
    Group = apps.get_model("auth", "Group")
    User = apps.get_model("main", "User")
    database = schema_editor.connection.alias
    admin_group, _ = Group.objects.using(database).get_or_create(
        name=ADMIN_GROUP_NAME
    )
    for user in User.objects.using(database).filter(is_superuser=True):
        user.groups.add(admin_group)


def remove_admin_group(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    """Remove the Admin group created by this migration."""
    Group = apps.get_model("auth", "Group")
    Group.objects.using(schema_editor.connection.alias).filter(
        name=ADMIN_GROUP_NAME
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_admin_group, remove_admin_group),
    ]
