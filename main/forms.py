"""Forms module for the main app."""

import json

from django import forms
from django.conf import settings

from .models import RegisteredSchema


class RegisteredSchemaAddForm(forms.ModelForm[RegisteredSchema]):
    """Form to register a schema by naming it and uploading a JSON file."""

    file = forms.FileField(label="Schema file", help_text="A UTF-8 encoded JSON file.")

    class Meta:
        """Form options."""

        model = RegisteredSchema
        fields = ("name",)

    def clean_file(self) -> object:
        """Parse the uploaded file as JSON and return the parsed value."""
        uploaded = self.cleaned_data["file"]
        if uploaded.size > settings.SCHEMA_UPLOAD_MAX_BYTES:
            raise forms.ValidationError(
                "The file is too large: %(size)s bytes. The maximum is %(max)s bytes.",
                params={
                    "size": f"{uploaded.size:,}",
                    "max": f"{settings.SCHEMA_UPLOAD_MAX_BYTES:,}",
                },
                code="too_large",
            )
        try:
            definition = json.loads(uploaded.read().decode("utf-8-sig"))
        except ValueError as error:  # includes UnicodeDecodeError
            raise forms.ValidationError(
                "The file is not valid JSON: %(error)s",
                params={"error": error},
                code="invalid_json",
            ) from error
        if definition is None:
            raise forms.ValidationError(
                "The file must contain a JSON Schema, not null.", code="null_schema"
            )
        self.cleaned_data["definition"] = definition
        return uploaded

    def save(self, commit: bool = True) -> RegisteredSchema:
        """Store the parsed JSON as the schema definition."""
        self.instance.definition = self.cleaned_data["definition"]
        return super().save(commit=commit)
