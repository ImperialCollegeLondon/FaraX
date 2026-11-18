"""Tests for registering schemas through Django Admin."""

from http import HTTPStatus

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from main.models import RegisteredSchema

SCHEMA = b'{"type": "object", "minimum": 1.5, "properties": {"a": {"type": "string"}}}'


ADD_URL = reverse("admin:main_registeredschema_add")
LIST_URL = reverse("admin:main_registeredschema_changelist")


def form_errors(response):
    """The errors on the admin form rendered in a response."""
    return response.context["adminform"].form.errors.as_data()


def upload(name, content=SCHEMA):
    """Build add-form data for a schema upload."""
    return {"name": name, "file": SimpleUploadedFile("s.json", content)}


def grant(user, *codenames):
    """Give a user the registered schema permissions with the given codenames."""
    user.user_permissions.set(
        Permission.objects.filter(
            content_type__app_label="main", codename__in=codenames
        )
    )


def test_upload_stores_parsed_json(superuser_client):
    """A valid upload creates a registration whose definition round-trips."""
    response = superuser_client.post(ADD_URL, upload("Co"))

    assert response.status_code == HTTPStatus.FOUND
    schema = RegisteredSchema.objects.get()
    assert schema.name == "Co"
    assert schema.definition == {
        "type": "object",
        "minimum": 1.5,
        "properties": {"a": {"type": "string"}},
    }


def test_change_view_shows_definition_read_only(superuser_client):
    """The change page shows the definition but has no input to edit it."""
    schema = RegisteredSchema.objects.create(name="Co", definition={"type": "string"})

    response = superuser_client.get(
        reverse("admin:main_registeredschema_change", args=[schema.pk])
    )

    assert response.status_code == HTTPStatus.OK
    assert b"&quot;type&quot;: &quot;string&quot;" in response.content
    assert b'name="definition"' not in response.content
    assert b'name="file"' not in response.content


def test_invalid_json_gives_error_and_creates_nothing(superuser_client):
    """A file that is not JSON is reported and nothing is registered."""
    response = superuser_client.post(ADD_URL, upload("Bad", b"{not json"))

    assert response.status_code == HTTPStatus.OK
    assert [e.code for e in form_errors(response)["file"]] == ["invalid_json"]
    assert not RegisteredSchema.objects.exists()


def test_non_utf8_file_gives_error(superuser_client):
    """A file that is not UTF-8 text is reported."""
    response = superuser_client.post(ADD_URL, upload("Bad", b"\xff\xfe\x00"))

    assert response.status_code == HTTPStatus.OK
    assert [e.code for e in form_errors(response)["file"]] == ["invalid_json"]
    assert not RegisteredSchema.objects.exists()


def test_null_file_gives_error_and_creates_nothing(superuser_client):
    """A file containing JSON null is reported rather than failing on save."""
    response = superuser_client.post(ADD_URL, upload("Null", b"null"))

    assert response.status_code == HTTPStatus.OK
    assert [e.code for e in form_errors(response)["file"]] == ["null_schema"]
    assert not RegisteredSchema.objects.exists()


def test_name_is_trimmed(superuser_client):
    """Surrounding whitespace is removed from the name."""
    superuser_client.post(ADD_URL, upload("  Co  "))

    assert RegisteredSchema.objects.get().name == "Co"


def test_blank_name_rejected(superuser_client):
    """A whitespace-only name is rejected."""
    response = superuser_client.post(ADD_URL, upload("   "))

    assert response.status_code == HTTPStatus.OK
    assert [e.code for e in form_errors(response)["name"]] == ["required"]
    assert not RegisteredSchema.objects.exists()


def test_name_length_limit_applies_after_trimming(superuser_client):
    """255 characters plus padding is accepted; 256 characters is not."""
    superuser_client.post(ADD_URL, upload(" " + "a" * 255 + " "))
    response = superuser_client.post(ADD_URL, upload("b" * 256))

    assert response.status_code == HTTPStatus.OK
    assert [e.code for e in form_errors(response)["name"]] == ["max_length"]
    assert list(RegisteredSchema.objects.values_list("name", flat=True)) == ["a" * 255]


def test_names_unique_but_case_sensitive(superuser_client):
    """`Co` and `CO` can coexist but an exact duplicate cannot."""
    superuser_client.post(ADD_URL, upload("Co"))
    superuser_client.post(ADD_URL, upload("CO"))
    response = superuser_client.post(ADD_URL, upload("Co"))

    assert response.status_code == HTTPStatus.OK
    assert [e.code for e in form_errors(response)["name"]] == ["unique"]
    assert sorted(RegisteredSchema.objects.values_list("name", flat=True)) == [
        "CO",
        "Co",
    ]


def test_anonymous_redirected_to_login(client, db):
    """Anonymous users cannot reach the schema pages."""
    for method in (client.get, client.post):
        response = method(ADD_URL)
        assert response.status_code == HTTPStatus.FOUND
        assert reverse("admin:login") in response["Location"]
    assert not RegisteredSchema.objects.exists()


def test_non_staff_redirected_to_login(client, django_user_model):
    """Logged-in non-staff users cannot reach the schema pages."""
    user = django_user_model.objects.create_user(username="u")
    user.user_permissions.set(
        Permission.objects.filter(codename__contains="registered")
    )
    client.force_login(user)

    assert client.get(LIST_URL).status_code == HTTPStatus.FOUND
    assert client.post(ADD_URL, upload("Co")).status_code == HTTPStatus.FOUND
    assert not RegisteredSchema.objects.exists()


def test_staff_without_permission_forbidden(staff_client):
    """Staff without schema permissions get 403 on direct URLs."""
    schema = RegisteredSchema.objects.create(name="Co", definition={})
    change_url = reverse("admin:main_registeredschema_change", args=[schema.pk])

    assert staff_client.get(LIST_URL).status_code == HTTPStatus.FORBIDDEN
    assert staff_client.get(ADD_URL).status_code == HTTPStatus.FORBIDDEN
    assert staff_client.post(ADD_URL, upload("X")).status_code == HTTPStatus.FORBIDDEN
    assert staff_client.get(change_url).status_code == HTTPStatus.FORBIDDEN
    assert RegisteredSchema.objects.count() == 1


def test_staff_with_add_permission_can_register(staff_user, staff_client):
    """Staff with the add permission can register a schema."""
    grant(staff_user, "add_registeredschema", "view_registeredschema")

    response = staff_client.post(ADD_URL, upload("Co"))

    assert response.status_code == HTTPStatus.FOUND
    assert RegisteredSchema.objects.filter(name="Co").exists()


def test_staff_with_view_permission_only_cannot_add(staff_user, staff_client):
    """Staff with only view permission can inspect but not register."""
    grant(staff_user, "view_registeredschema")
    schema = RegisteredSchema.objects.create(name="Co", definition={"a": 1})
    change_url = reverse("admin:main_registeredschema_change", args=[schema.pk])

    assert staff_client.get(change_url).status_code == HTTPStatus.OK
    assert staff_client.get(ADD_URL).status_code == HTTPStatus.FORBIDDEN
    assert staff_client.post(ADD_URL, upload("X")).status_code == HTTPStatus.FORBIDDEN
    assert RegisteredSchema.objects.count() == 1
