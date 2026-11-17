"""Tests for the Django admin site."""

from http import HTTPStatus

from django.contrib.auth.models import Group


def create_admin(django_user_model):
    """Create an ordinary Admin account."""
    user = django_user_model.objects.create_user(
        username="ordinary-admin", password="secret", is_staff=True
    )
    user.groups.add(Group.objects.get(name="Admin"))
    return user


def test_admin_login_page_renders(client):
    """The admin login page is served to anonymous users."""
    response = client.get("/admin/login/")
    assert response.status_code == HTTPStatus.OK
    assert b"Log in" in response.content


def test_superuser_can_log_in_and_reach_admin_index(client, django_user_model):
    """A superuser logging in through the admin login form reaches the admin index."""
    user = django_user_model.objects.create_superuser(
        username="admin", password="secret"
    )
    assert user.is_admin

    response = client.post(
        "/admin/login/?next=/admin/",
        {"username": "admin", "password": "secret"},
        follow=True,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.redirect_chain == [("/admin/", HTTPStatus.FOUND)]
    assert b"Site administration" in response.content
    assert b"Users" in response.content


def test_admin_role_can_access_django_admin(client, django_user_model):
    """An ordinary Admin can enter Django Admin without being a superuser."""
    user = create_admin(django_user_model)
    client.force_login(user)

    response = client.get("/admin/")

    assert response.status_code == HTTPStatus.OK
    assert not user.is_superuser


def test_staff_user_without_admin_role_cannot_enter_django_admin(
    client, django_user_model
):
    """Staff status alone does not grant access to Django Admin."""
    user = django_user_model.objects.create_user(
        username="staff", password="secret", is_staff=True
    )
    client.force_login(user)

    response = client.get("/admin/")

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == "/admin/login/?next=/admin/"


def test_ordinary_admin_can_create_and_reset_a_user_password(client, django_user_model):
    """Ordinary Admins can provision accounts and set their passwords."""
    client.force_login(create_admin(django_user_model))
    add_response = client.post(
        "/admin/main/user/add/",
        {
            "username": "colleague",
            "password1": "a-strong-password-123",
            "password2": "a-strong-password-123",
        },
    )

    assert add_response.status_code == HTTPStatus.FOUND
    user = django_user_model.objects.get(username="colleague")
    assert user.check_password("a-strong-password-123")
    assert not user.is_staff
    assert not user.is_admin

    password_response = client.post(
        f"/admin/main/user/{user.pk}/password/",
        {
            "password1": "a-new-strong-password-456",
            "password2": "a-new-strong-password-456",
        },
    )

    assert password_response.status_code == HTTPStatus.FOUND
    user.refresh_from_db()
    assert user.check_password("a-new-strong-password-456")


def test_ordinary_admin_cannot_assign_admin_role_or_staff_status(
    client, django_user_model
):
    """Forged form fields cannot promote an account to Admin or staff."""
    client.force_login(create_admin(django_user_model))
    user = django_user_model.objects.create_user(
        username="colleague", password="secret"
    )

    response = client.post(
        f"/admin/main/user/{user.pk}/change/",
        {
            "username": user.username,
            "password": user.password,
            "date_joined": user.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
            "first_name": "",
            "last_name": "",
            "email": "",
            "is_active": "on",
            "is_staff": "on",
            "is_superuser": "on",
            "groups": [str(Group.objects.get(name="Admin").pk)],
            "_save": "Save",
        },
    )

    assert response.status_code == HTTPStatus.FOUND, response.context[
        "adminform"
    ].form.errors
    user.refresh_from_db()
    assert not user.is_admin
    assert not user.is_staff
    assert not user.is_superuser


def test_superuser_can_assign_and_revoke_admin_role(client, django_user_model):
    """Only a superuser can assign the Admin role."""
    superuser = django_user_model.objects.create_superuser(
        username="bootstrap", password="secret"
    )
    user = django_user_model.objects.create_user(
        username="colleague", password="secret"
    )
    admin_group = Group.objects.get(name="Admin")
    client.force_login(superuser)

    response = client.post(
        f"/admin/main/user/{user.pk}/change/",
        {
            "username": user.username,
            "password": user.password,
            "date_joined": user.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
            "first_name": "",
            "last_name": "",
            "email": "",
            "is_active": "on",
            "is_staff": "on",
            "groups": [str(admin_group.pk)],
            "_save": "Save",
        },
    )

    assert response.status_code == HTTPStatus.FOUND, response.context[
        "adminform"
    ].form.errors
    user.refresh_from_db()
    assert user.is_admin
    assert user.is_staff
    assert not user.is_superuser

    client.post(
        f"/admin/main/user/{user.pk}/change/",
        {
            "username": user.username,
            "password": user.password,
            "date_joined": user.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
            "first_name": "",
            "last_name": "",
            "email": "",
            "is_active": "on",
            "_save": "Save",
        },
    )

    user.refresh_from_db()
    assert not user.is_admin
    assert not user.is_staff


def test_superuser_cannot_downgrade_bootstrap_account_in_admin(
    client, django_user_model
):
    """The bootstrap account remains an Admin superuser after an admin edit."""
    superuser = django_user_model.objects.create_superuser(
        username="bootstrap", password="secret"
    )
    client.force_login(superuser)

    client.post(
        f"/admin/main/user/{superuser.pk}/change/",
        {
            "username": superuser.username,
            "date_joined": superuser.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
            "first_name": "",
            "last_name": "",
            "email": "",
            "is_active": "on",
            "_save": "Save",
        },
    )

    superuser.refresh_from_db()
    assert superuser.is_superuser
    assert superuser.is_staff
    assert superuser.is_admin


def test_ordinary_admin_cannot_revoke_another_admin_role(client, django_user_model):
    """Ordinary Admins can manage accounts without changing their Admin role."""
    client.force_login(create_admin(django_user_model))
    other_admin = django_user_model.objects.create_user(
        username="another-admin", password="secret", is_staff=True
    )
    other_admin.groups.add(Group.objects.get(name="Admin"))

    response = client.post(
        f"/admin/main/user/{other_admin.pk}/change/",
        {
            "username": other_admin.username,
            "password": other_admin.password,
            "first_name": "Updated",
            "last_name": "",
            "email": "",
            "is_active": "on",
            "groups": [],
            "is_staff": "",
            "_save": "Save",
        },
    )

    assert response.status_code == HTTPStatus.FOUND, response.context[
        "adminform"
    ].form.errors
    other_admin.refresh_from_db()
    assert other_admin.first_name == "Updated"
    assert other_admin.is_admin
    assert other_admin.is_staff

    delete_response = client.post(
        f"/admin/main/user/{other_admin.pk}/delete/", {"post": "yes"}
    )

    assert delete_response.status_code == HTTPStatus.FORBIDDEN
    assert django_user_model.objects.filter(pk=other_admin.pk).exists()
