"""Tests for local sign-in and application access."""

from http import HTTPStatus

import pytest
from django.contrib.auth.models import Group
from django.test import Client, override_settings


@pytest.fixture(autouse=True)
def auth_urls():
    """Use test-only application routes to exercise access boundaries."""
    with override_settings(ROOT_URLCONF="tests.auth_urls"):
        yield


def test_anonymous_protected_request_redirects_to_login(client):
    """Protected application routes retain their destination through sign-in."""
    response = client.get("/protected/?query=value")

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == "/accounts/login/?next=/protected/%3Fquery%3Dvalue"


def test_login_honours_safe_destination(client, django_user_model):
    """Valid local credentials establish a session and return to a safe destination."""
    django_user_model.objects.create_user(username="colleague", password="secret")

    response = client.post(
        "/accounts/login/?next=/protected/%3Fquery%3Dvalue",
        {
            "username": "colleague",
            "password": "secret",
            "next": "/protected/?query=value",
        },
        follow=True,
    )

    assert response.redirect_chain == [("/protected/?query=value", HTTPStatus.FOUND)]
    assert response.content == b"Protected"


@pytest.mark.parametrize(
    "destination", [None, "", "https://evil.example/", "//evil.example/"]
)
def test_login_without_safe_destination_confirms_sign_in(
    client, django_user_model, destination
):
    """Without a safe destination, sign-in returns to the confirmation page."""
    django_user_model.objects.create_user(username="colleague", password="secret")
    data = {"username": "colleague", "password": "secret"}
    if destination is not None:
        data["next"] = destination

    response = client.post("/accounts/login/", data, follow=True)

    assert response.redirect_chain == [("/accounts/login/", HTTPStatus.FOUND)]
    assert b"Signed in" in response.content
    assert client.get("/protected/").status_code == HTTPStatus.OK


def test_invalid_credentials_do_not_authenticate(client, django_user_model):
    """Incorrect credentials leave the visitor signed out."""
    django_user_model.objects.create_user(username="colleague", password="secret")

    response = client.post(
        "/accounts/login/", {"username": "colleague", "password": "incorrect"}
    )

    assert response.status_code == HTTPStatus.OK
    assert "_auth_user_id" not in client.session
    assert client.get("/protected/").status_code == HTTPStatus.FOUND


def test_admin_action_requires_admin_role(client, django_user_model):
    """Anonymous, non-Admin and Admin users meet the correct access boundary."""
    assert client.get("/admin-action/")["Location"] == (
        "/accounts/login/?next=/admin-action/"
    )
    user = django_user_model.objects.create_user(
        username="colleague", password="secret"
    )
    client.force_login(user)
    assert client.get("/admin-action/").status_code == HTTPStatus.FORBIDDEN

    user.groups.add(Group.objects.get(name="Admin"))
    assert client.get("/admin-action/").status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    "path", ["/accounts/password/change/", "/accounts/password/change/done/"]
)
def test_anonymous_users_are_redirected_to_sign_in(client, path):
    """The password change form and confirmation require authentication."""
    response = client.get(path)

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == f"/accounts/login/?next={path}"


def test_password_change_updates_only_current_user_and_preserves_session(
    client, django_user_model
):
    """A valid password change affects the signed-in account and keeps it signed in."""
    user = django_user_model.objects.create_user(
        username="colleague", password="old-pass-123"
    )
    other = django_user_model.objects.create_user(
        username="other", password="other-pass-123"
    )
    client.force_login(user)

    response = client.post(
        "/accounts/password/change/",
        {
            "old_password": "old-pass-123",
            "new_password1": "a-new-strong-password-456",
            "new_password2": "a-new-strong-password-456",
        },
        follow=True,
    )

    assert response.redirect_chain == [
        ("/accounts/password/change/done/", HTTPStatus.FOUND)
    ]
    assert b"Password changed" in response.content
    assert client.get("/accounts/password/change/").status_code == HTTPStatus.OK
    other.refresh_from_db()
    assert other.check_password("other-pass-123")
    assert not Client().login(username="colleague", password="old-pass-123")
    assert Client().login(username="colleague", password="a-new-strong-password-456")


@pytest.mark.parametrize(
    ("old_password", "new_password1", "new_password2", "error"),
    [
        (
            "wrong-password",
            "a-new-strong-password-456",
            "a-new-strong-password-456",
            "old_password",
        ),
        ("old-pass-123", "123", "123", "new_password2"),
        (
            "old-pass-123",
            "a-new-strong-password-456",
            "different-password-456",
            "new_password2",
        ),
    ],
)
def test_invalid_password_change_is_rejected(
    client, django_user_model, old_password, new_password1, new_password2, error
):
    """Incorrect current passwords, weak passwords and mismatches are rejected."""
    user = django_user_model.objects.create_user(
        username="colleague", password="old-pass-123"
    )
    client.force_login(user)

    response = client.post(
        "/accounts/password/change/",
        {
            "old_password": old_password,
            "new_password1": new_password1,
            "new_password2": new_password2,
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert error in response.context["form"].errors
    assert Client().login(username="colleague", password="old-pass-123")


def test_password_change_link_is_available_to_signed_in_users(
    client, django_user_model
):
    """A signed-in user can find the password change form."""
    user = django_user_model.objects.create_user(
        username="colleague", password="old-pass-123"
    )
    client.force_login(user)

    response = client.get("/accounts/login/")

    assert b'href="/accounts/password/change/"' in response.content


@pytest.mark.parametrize(
    "path",
    ["/accounts/login/", "/accounts/password/change/", "/accounts/password/change/done/"],
)
def test_account_pages_show_farax_banner(client, django_user_model, path):
    """Sign-in and password-change pages share the FaraX banner."""
    user = django_user_model.objects.create_user(username="colleague", password="secret")
    client.force_login(user)

    response = client.get(path)

    assert response.status_code == HTTPStatus.OK
    assert b"Data management for materials discovery" in response.content
