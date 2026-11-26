"""Tests for the Django admin site."""

from http import HTTPStatus

from django.contrib.auth.models import Group
from django.urls import reverse


def test_admin_login_page_renders(client):
    """The admin login page is served to anonymous users."""
    response = client.get(reverse("admin:login"))
    assert response.status_code == HTTPStatus.OK
    assert b"Log in" in response.content


def test_superuser_can_log_in_and_reach_admin_index(client, django_user_model):
    """A superuser logging in through the admin login form reaches the admin index."""
    django_user_model.objects.create_superuser(username="admin", password="secret")
    admin_index = reverse("admin:index")

    response = client.post(
        f"{reverse('admin:login')}?next={admin_index}",
        {"username": "admin", "password": "secret"},
        follow=True,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.redirect_chain == [(admin_index, HTTPStatus.FOUND)]
    assert b"Site administration" in response.content
    assert b"Users" in response.content


def test_assigning_admin_group_grants_staff(superuser_client, django_user_model):
    """Assigning the Admin group through Django Admin grants staff status."""
    user = django_user_model.objects.create_user(username="new-admin")
    admin_group = Group.objects.get(name="Admin")

    superuser_client.post(
        reverse("admin:main_user_change", args=[user.pk]),
        {
            "username": user.username,
            "is_active": "on",
            "groups": [admin_group.pk],
            "date_joined_0": "2026-01-01",
            "date_joined_1": "00:00:00",
        },
    )

    user.refresh_from_db()
    assert user.is_staff
    assert user.groups.filter(pk=admin_group.pk).exists()


def test_admin_cannot_grant_superuser(client, group_admin, django_user_model):
    """An Admin cannot make themselves or anyone else a superuser."""
    other = django_user_model.objects.create_user(username="other", password="secret")
    client.force_login(group_admin)

    for target in (group_admin, other):
        data = {
            "username": target.username,
            "is_active": "on",
            "is_staff": "on" if target.is_staff else "",
            "is_superuser": "on",
            "date_joined_0": "2026-01-01",
            "date_joined_1": "00:00:00",
        }
        client.post(reverse("admin:main_user_change", args=[target.pk]), data)
        target.refresh_from_db()
        assert not target.is_superuser


def test_admin_can_manage_normal_users(client, group_admin, django_user_model):
    """An Admin can see and open ordinary users."""
    other = django_user_model.objects.create_user(username="other", password="secret")
    client.force_login(group_admin)

    changelist = client.get(reverse("admin:main_user_changelist"))
    assert changelist.status_code == HTTPStatus.OK
    response = client.get(reverse("admin:main_user_change", args=[other.pk]))
    assert response.status_code == HTTPStatus.OK


def test_admin_cannot_change_or_delete_superuser(
    client, group_admin, django_user_model
):
    """An Admin cannot edit or delete a superuser account."""
    superuser = django_user_model.objects.create_superuser(username="root")
    client.force_login(group_admin)

    change = client.post(
        reverse("admin:main_user_change", args=[superuser.pk]),
        {"username": "renamed"},
    )
    delete = client.post(
        reverse("admin:main_user_delete", args=[superuser.pk]), {"post": "yes"}
    )

    assert change.status_code == HTTPStatus.FORBIDDEN
    assert delete.status_code == HTTPStatus.FORBIDDEN
    superuser.refresh_from_db()
    assert superuser.username == "root"


def test_superuser_keeps_full_control(superuser_client, group_admin):
    """A superuser can still edit and delete other staff and see bulk delete."""
    response = superuser_client.get(
        reverse("admin:main_user_change", args=[group_admin.pk])
    )
    assert response.status_code == HTTPStatus.OK
    changelist = superuser_client.get(reverse("admin:main_user_changelist"))
    assert b"delete_selected" in changelist.content


def test_admin_group_has_only_user_and_schema_permissions(db):
    """The Admin group receives only permissions to manage users and schemas."""
    group = Group.objects.get(name="Admin")

    assert set(group.permissions.values_list("codename", flat=True)) == {
        "add_user",
        "change_user",
        "delete_user",
        "view_user",
        "add_registeredschema",
        "change_registeredschema",
        "delete_registeredschema",
        "view_registeredschema",
    }


def test_non_staff_user_cannot_use_admin(client, django_user_model):
    """A user who is not staff is turned away from the admin site."""
    django_user_model.objects.create_user(username="plain", password="secret")
    client.login(username="plain", password="secret")

    response = client.get(reverse("admin:index"))

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"].startswith(reverse("admin:login"))
