"""URL configuration for the FaraX project.

`urlpatterns` maps URL paths to the Django admin and local authentication views.
See https://docs.djangoproject.com/en/6.1/topics/http/urls/.
"""

from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path

from main.views import FaraXLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", FaraXLoginView.as_view(), name="login"),
    path("accounts/logout/", LogoutView.as_view(next_page="login"), name="logout"),
]
