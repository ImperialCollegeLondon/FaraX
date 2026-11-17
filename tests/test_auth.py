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
