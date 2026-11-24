"""Shared fixtures for the test suite."""

import pytest
from django.contrib.auth.models import Group


@pytest.fixture
def superuser_client(client, django_user_model):
    """A client logged in as a superuser."""
    user = django_user_model.objects.create_superuser(username="root")
    client.force_login(user)
    return client


@pytest.fixture
def staff_user(django_user_model):
    """An active staff user with no permissions."""
    return django_user_model.objects.create_user(username="staff", is_staff=True)


@pytest.fixture
def staff_client(client, staff_user):
    """A client logged in as `staff_user`."""
    client.force_login(staff_user)
    return client


@pytest.fixture
def group_admin(django_user_model):
    """A staff user in the Admin group who is not a superuser."""
    user = django_user_model.objects.create_user(
        username="admin", password="secret", is_staff=True
    )
    user.groups.add(Group.objects.get(name="Admin"))
    return user
