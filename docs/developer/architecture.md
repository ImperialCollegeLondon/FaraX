# Architecture

FaraX is a single [Django] project at the root of the repository (see
[ADR 0001](../adr/0001-single-repository.md)). It was generated with `django-admin
startproject` and `startapp`, so it follows the standard Django layout.

```text
manage.py        Django's command-line utility (migrate, runserver, createsuperuser, ...)
farax/           the Django project package
    settings/    settings package; `farax.settings` loads the base settings
        base.py  base settings, suitable for local development
    urls.py      root URL configuration; the admin is served at /admin/
    asgi.py      ASGI entry point
    wsgi.py      WSGI entry point
main/            the single Django app
    models.py    database models, including the custom User model
    admin.py     Django admin registrations
    migrations/  database migrations, generated with `makemigrations`
db/              git-ignored directory holding the local SQLite database
tests/           the test suite, run with pytest and pytest-django
```

The `farax` package also provides `farax.__version__`, derived from git tags by
`setuptools-scm`.

## User model

`main.User` is a custom user model that subclasses Django's `AbstractUser` and adds no
fields. It is the configured `AUTH_USER_MODEL` and is created by the first migration, so
that it can be extended later without a difficult migration. Code should refer to it
through `django.contrib.auth.get_user_model()` or `settings.AUTH_USER_MODEL` rather than
importing Django's built-in `User`.

## Database

Local development uses SQLite with no configuration. Production uses PostgreSQL (see
[ADR 0002](../adr/0002-postgresql-with-sqlite-for-local-development.md)).

[Django]: https://www.djangoproject.com/
