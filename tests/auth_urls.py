"""Test-only routes for application authentication boundaries."""

from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest, HttpResponse
from django.urls import include, path

from main.auth import admin_required


def protected(request: HttpRequest) -> HttpResponse:
    """Return a protected application response."""
    return HttpResponse("Protected")


@admin_required
def admin_action(request: HttpRequest) -> HttpResponse:
    """Return an Admin-only application response."""
    return HttpResponse("Admin action")


@login_not_required
def public(request: HttpRequest) -> HttpResponse:
    """Return a public application response."""
    return HttpResponse("Public")


urlpatterns = [
    path("protected/", protected),
    path("admin-action/", admin_action),
    path("public/", public),
    path("", include("farax.urls")),
]
