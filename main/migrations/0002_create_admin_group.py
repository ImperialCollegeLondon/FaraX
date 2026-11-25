"""Create the Admin group with permissions to manage user accounts."""

from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps


ADMIN_GROUP_NAME = "Admin"
USER_PERMISSION_NAMES = {
    "add_user": "Can add user",
    "change_user": "Can change user",
    "delete_user": "Can delete user",
    "view_user": "Can view user",
}


def create_admin_group(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    """Create the Admin group and grant only user-account permissions."""
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    database = schema_editor.connection.alias

    content_type, _ = ContentType.objects.using(database).get_or_create(
        app_label="main", model="user"
    )
    permissions = [
        Permission.objects.using(database).get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": name},
        )[0]
        for codename, name in USER_PERMISSION_NAMES.items()
    ]
    group, _ = Group.objects.using(database).get_or_create(name=ADMIN_GROUP_NAME)
    group.permissions.set(permissions)

    # Make all Users in 'Admin' group also Staff
    User = apps.get_model("main", "User")
    User.objects.using(database).filter(groups=group).update(is_staff=True)


def remove_admin_group(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    """Remove the Admin group when reversing this migration."""
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
