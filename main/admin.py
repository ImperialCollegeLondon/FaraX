"""Admin site registrations for the main app."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import QuerySet
from django.forms import ModelForm
from django.forms.models import BaseInlineFormSet
from django.http import HttpRequest

from .models import ADMIN_GROUP_NAME, User

if TYPE_CHECKING:
    from django.contrib.admin.options import _FieldsetSpec


class FaraXUserAdmin(UserAdmin):  # type: ignore[type-arg]
    """Let Admins manage accounts without granting them role privileges."""

    actions = None
    readonly_fields = ("last_login", "date_joined")

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        """Hide the controlled superuser account from ordinary Admins."""
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.exclude(is_superuser=True)

    def get_fieldsets(
        self, request: HttpRequest, obj: User | None = None
    ) -> _FieldsetSpec:
        """Hide role and staff controls from ordinary Admins."""
        if request.user.is_superuser:
            return super().get_fieldsets(request, obj)
        if obj is None:
            return [(None, {"fields": ("username", "password1", "password2")})]
        return [
            (None, {"fields": ("username", "password")}),
            ("Personal info", {"fields": ("first_name", "last_name", "email")}),
            ("Permissions", {"fields": ("is_active",)}),
        ]

    def save_model(
        self, request: HttpRequest, obj: User, form: ModelForm[User], change: bool
    ) -> None:
        """Keep existing superusers from being downgraded in Django Admin."""
        if (
            change
            and obj.pk is not None
            and User.objects.filter(pk=obj.pk, is_superuser=True).exists()
        ):
            obj.is_superuser = True
            obj.is_staff = True
        super().save_model(request, obj, form, change)

    def save_related(
        self,
        request: HttpRequest,
        form: ModelForm[User],
        formsets: list[BaseInlineFormSet[User, User, ModelForm[User]]],
        change: bool,
    ) -> None:
        """Keep staff access consistent with the Admin role."""
        super().save_related(request, form, formsets, change)
        user = form.instance
        if user.is_superuser:
            admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP_NAME)
            user.groups.add(admin_group)
        user.is_staff = user.is_superuser or user.is_admin
        user.save(update_fields=["is_staff"])

    def has_module_permission(self, request: HttpRequest) -> bool:
        """Allow Admin-role users to see the user-management module."""
        return request.user.is_authenticated and request.user.is_admin

    def has_view_permission(
        self, request: HttpRequest, obj: User | None = None
    ) -> bool:
        """Allow Admin-role users to view accounts except the bootstrap superuser."""
        return (
            request.user.is_authenticated
            and request.user.is_admin
            and (obj is None or request.user.is_superuser or not obj.is_superuser)
        )

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Allow Admin-role users to create accounts."""
        return request.user.is_authenticated and request.user.is_admin

    def has_change_permission(
        self, request: HttpRequest, obj: User | None = None
    ) -> bool:
        """Allow Admin-role users to change accounts except the bootstrap superuser."""
        return (
            request.user.is_authenticated
            and request.user.is_admin
            and (obj is None or request.user.is_superuser or not obj.is_superuser)
        )

    def has_delete_permission(
        self, request: HttpRequest, obj: User | None = None
    ) -> bool:
        """Allow Admin-role users to delete accounts except the bootstrap superuser."""
        return (
            request.user.is_authenticated
            and request.user.is_admin
            and (
                obj is None
                or request.user.is_superuser
                or (not obj.is_superuser and not obj.is_admin)
            )
        )


admin.site.unregister(Group)
admin.site.register(User, FaraXUserAdmin)
