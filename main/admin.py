"""Admin site registrations for the main app."""

import json

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpRequest

from .forms import RegisteredSchemaAddForm
from .models import RegisteredSchema, User

admin.site.register(User, UserAdmin)


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
