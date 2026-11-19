"""Tests for the Django admin site."""

from http import HTTPStatus

import pytest

from main.admin import ensure_full_admin_group


def test_admin_login_page_renders(client):
    """The admin login page is served to anonymous users."""
    response = client.get("/admin/login/")
    assert response.status_code == HTTPStatus.OK
    assert b"Log in" in response.content


def test_superuser_can_log_in_and_reach_admin_index(client, django_user_model):
    """A superuser logging in through the admin login form reaches the admin index."""
    django_user_model.objects.create_superuser(username="admin", password="secret")

    response = client.post(
        "/admin/login/?next=/admin/",
        {"username": "admin", "password": "secret"},
        follow=True,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.redirect_chain == [("/admin/", HTTPStatus.FOUND)]
    assert b"Site administration" in response.content
    assert b"Users" in response.content


@pytest.fixture
def full_admin(django_user_model):
    """A staff user in the full-admin group who is not a superuser."""
    user = django_user_model.objects.create_user(
        username="full", password="secret", is_staff=True
    )
    user.groups.add(ensure_full_admin_group())
    return user


@pytest.fixture
def superuser(django_user_model):
    """A superuser."""
    return django_user_model.objects.create_superuser(
        username="root", password="secret"
    )


def test_full_admin_cannot_grant_superuser(client, full_admin, django_user_model):
    """A full admin cannot make themselves or anyone else a superuser."""
    other = django_user_model.objects.create_user(username="other", password="secret")
    client.force_login(full_admin)

    for target in (full_admin, other):
        data = {
            "username": target.username,
            "is_active": "on",
            "is_staff": "on" if target.is_staff else "",
            "is_superuser": "on",
            "date_joined_0": "2026-01-01",
            "date_joined_1": "00:00:00",
        }
        client.post(f"/admin/main/user/{target.pk}/change/", data)
        target.refresh_from_db()
        assert not target.is_superuser


def test_full_admin_can_manage_normal_users(client, full_admin, django_user_model):
    """A full admin can see and open ordinary users."""
    other = django_user_model.objects.create_user(username="other", password="secret")
    client.force_login(full_admin)

    assert client.get("/admin/main/user/").status_code == HTTPStatus.OK
    response = client.get(f"/admin/main/user/{other.pk}/change/")
    assert response.status_code == HTTPStatus.OK


def test_full_admin_cannot_change_or_delete_superuser(client, full_admin, superuser):
    """A full admin cannot edit or delete a superuser account."""
    client.force_login(full_admin)

    change = client.post(
        f"/admin/main/user/{superuser.pk}/change/", {"username": "renamed"}
    )
    delete = client.post(f"/admin/main/user/{superuser.pk}/delete/", {"post": "yes"})

    assert change.status_code == HTTPStatus.FORBIDDEN
    assert delete.status_code == HTTPStatus.FORBIDDEN
    superuser.refresh_from_db()
    assert superuser.username == "root"


def test_superuser_keeps_full_control(client, superuser, full_admin):
    """A superuser can still edit and delete other staff and see bulk delete."""
    client.force_login(superuser)

    response = client.get(f"/admin/main/user/{full_admin.pk}/change/")
    assert response.status_code == HTTPStatus.OK
    assert b"delete_selected" in client.get("/admin/main/user/").content


def test_non_staff_user_cannot_use_admin(client, django_user_model):
    """A user who is not staff is turned away from the admin site."""
    django_user_model.objects.create_user(username="plain", password="secret")
    client.login(username="plain", password="secret")

    response = client.get("/admin/")

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"].startswith("/admin/login/")
