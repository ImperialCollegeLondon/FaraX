"""URL configuration for the FaraX project.

`urlpatterns` maps URL paths to views. It currently serves only the Django admin at
`/admin/`. See https://docs.djangoproject.com/en/6.1/topics/http/urls/.
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
