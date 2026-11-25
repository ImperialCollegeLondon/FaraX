"""Admin site registrations for the main app.

There are three kinds of account:

1. Superusers have unrestricted access.
2. Staff in the "Admin" group can manage user accounts, but cannot make anyone a
   superuser or change or delete a superuser.
3. Everyone else is not staff, so Django does not let them into the admin site at all.
"""

import json

from django import forms
from django.contrib import admin
from django.contrib.admin.options import Action, ActionLocation
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest

from .forms import RegisteredSchemaAddForm
from .models import RegisteredSchema, User


@admin.register(RegisteredSchema)
class RegisteredSchemaAdmin(admin.ModelAdmin[RegisteredSchema]):
    """Admin for registered schemas: upload on add, read-only definition after."""

    list_display = ("name",)
    search_fields = ("name",)
    readonly_fields = ("pretty_definition",)

    def get_form(
        self,
        request: HttpRequest,
        obj: RegisteredSchema | None = None,
        change: bool = False,
        **kwargs: object,
    ) -> type[forms.ModelForm[RegisteredSchema]]:
        """Use the upload form when adding."""
        if obj is None:
            kwargs["form"] = RegisteredSchemaAddForm
        return super().get_form(request, obj, change, **kwargs)

    def get_fields(
        self, request: HttpRequest, obj: RegisteredSchema | None = None
    ) -> tuple[str, ...]:
        """Show the upload field when adding and the definition when viewing."""
        return ("name", "file") if obj is None else ("name", "pretty_definition")

    @admin.display(description="Definition")
    def pretty_definition(self, obj: RegisteredSchema) -> str:
        """Return the definition as indented JSON."""
        return json.dumps(obj.definition, indent=2)


class SafeUserAdmin(DjangoUserAdmin[User]):
    """Restrict users in the Admin group from changing supersuser status.

    Non-superusers cannot grant superuser status or change or delete superuser
    accounts.
    """

    def get_form(
        self,
        request: HttpRequest,
        obj: User | None = None,
        change: bool = False,
        **kwargs: object,
    ) -> type[ModelForm[User]]:
        """Never let a non-superuser edit the `is_superuser` field."""
        form = super().get_form(request, obj, change=change, **kwargs)
        if not request.user.is_superuser and "is_superuser" in form.base_fields:
            form.base_fields["is_superuser"].disabled = True
        return form

    def save_model(
        self, request: HttpRequest, obj: User, form: ModelForm[User], change: bool
    ) -> None:
        """Enforce staff and superuser rules when saving a user."""
        groups: QuerySet[Group] | None = form.cleaned_data.get("groups")
        if groups is not None and groups.filter(name="Admin").exists():
            obj.is_staff = True
        if not request.user.is_superuser:
            obj.is_superuser = False
        super().save_model(request, obj, form, change)

    def has_change_permission(
        self, request: HttpRequest, obj: User | None = None
    ) -> bool:
        """Only superusers can change superuser accounts."""
        if not super().has_change_permission(request, obj):
            return False
        return request.user.is_superuser or obj is None or not obj.is_superuser

    def has_delete_permission(
        self, request: HttpRequest, obj: User | None = None
    ) -> bool:
        """Only superusers can delete superuser accounts."""
        if not super().has_delete_permission(request, obj):
            return False
        return request.user.is_superuser or obj is None or not obj.is_superuser

    def get_actions(
        self,
        request: HttpRequest,
        action_location: ActionLocation = ActionLocation.CHANGE_LIST,
    ) -> dict[str, Action | None]:
        """Remove bulk delete for non-superusers, as it skips the per-user check."""
        actions = super().get_actions(request, action_location)
        if not request.user.is_superuser:
            actions.pop("delete_selected", None)
        return actions

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        """Never delete superusers on behalf of a non-superuser."""
        if not request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True)
        super().delete_queryset(request, queryset)


# A model can only be registered once, so remove any existing registration first.
if admin.site.is_registered(User):
    admin.site.unregister(User)
admin.site.register(User, SafeUserAdmin)
