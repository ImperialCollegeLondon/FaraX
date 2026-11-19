"""Admin site registrations for the main app.

There are three kinds of account:

1. Superusers have unrestricted access.
2. Staff in the "Full Admin (non-superuser)" group can do everything in the admin site
   except make anyone a superuser or change or delete a superuser. Create the group
   with `ensure_full_admin_group` and add staff users to it.
3. Everyone else is not staff, so Django does not let them into the admin site at all.
"""

from django.contrib import admin
from django.contrib.admin.options import Action, ActionLocation
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group, Permission
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest

from .models import User

FULL_ADMIN_GROUP_NAME = "Full Admin (non-superuser)"


def ensure_full_admin_group() -> Group:
    """Create the full-admin group if needed and give it every permission.

    It is safe to call repeatedly. There is no Django permission for becoming a
    superuser, so granting all permissions is safe as long as `SafeUserAdmin` guards the
    `is_superuser` field.
    """
    group, _ = Group.objects.get_or_create(name=FULL_ADMIN_GROUP_NAME)
    group.permissions.set(Permission.objects.all())
    return group


class SafeUserAdmin(DjangoUserAdmin):  # type: ignore[type-arg]
    """Behaves exactly like the stock UserAdmin (so "full access" is preserved),
    with two extra guards layered on top:

    * Non-superusers can never set is_superuser=True on anyone.
    (Django's UserAdmin.get_form already disables this field for
    non-superusers — kept here as an explicit, visible guarantee.)

    * Non-superusers can never change or delete an account that is
    already a superuser. They can still see it in the list / open it
    read-only, but the form is rendered disabled and save/delete is
    blocked server-side.
    """  # noqa: D205, D415

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
        """Force `is_superuser` off for non-superusers, whatever was submitted."""
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
