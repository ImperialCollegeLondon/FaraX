"""Tests for the Django admin site."""

from http import HTTPStatus


def test_admin_login_page_renders(client):
    """The admin login page is served to anonymous users."""
    response = client.get("/admin/login/")
    assert response.status_code == HTTPStatus.OK
    assert b"Log in" in response.content
