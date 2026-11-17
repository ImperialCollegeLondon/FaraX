"""Django Admin application configuration for FaraX."""

from django.contrib.admin.apps import AdminConfig


class MainAdminConfig(AdminConfig):
    """Use FaraX's role-aware Django Admin site."""

    default_site = "main.admin_site.FaraXAdminSite"
