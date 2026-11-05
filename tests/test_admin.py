"""Tests for the Django admin site."""

from http import HTTPStatus


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
