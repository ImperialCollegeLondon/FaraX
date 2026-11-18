"""Django Admin application configuration for FaraX."""

from django.contrib import admin
from django.contrib.admin.apps import AdminConfig
from django.http import HttpRequest


class FaraXAdminSite(admin.AdminSite):
    """Only allow Admin-role users into Django Admin."""

    def has_permission(self, request: HttpRequest) -> bool:
        """Check that the active staff user has the Admin role."""
        return (
            super().has_permission(request)
            and request.user.is_authenticated
            and request.user.is_admin
        )


class MainAdminConfig(AdminConfig):
    """Use FaraX's role-aware Django Admin site."""

    default_site = "main.admin_apps.FaraXAdminSite"
