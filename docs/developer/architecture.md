# Architecture

FaraX is a single [Django] project at the root of the repository (see
[ADR 0001](../adr/0001-single-repository.md)). It was generated with `django-admin
startproject` and `startapp`, so it follows the standard Django layout.

```text
manage.py        Django's command-line utility (migrate, runserver, createsuperuser, ...)
farax/           the Django project package
    settings/    settings package; `farax.settings` loads the base settings
        base.py  base settings, suitable for local development
        production.py  production settings, configured by environment variables
    urls.py      root URL configuration; the admin is served at /admin/
    asgi.py      ASGI entry point
    wsgi.py      WSGI entry point
main/            the single Django app
    models.py    database models, including the custom User model
    admin.py     Django admin registrations
    migrations/  database migrations, generated with `makemigrations`
db/              git-ignored directory holding the local SQLite database
media/           git-ignored File Store, where Raw Files are kept
staticfiles/     git-ignored static files, written by `collectstatic`
tests/           the test suite, run with pytest and pytest-django
Dockerfile       image for the development Docker Compose stack
docker-compose.yml  development Docker Compose stack: the web app and PostgreSQL
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

Local development uses SQLite with no configuration. Production and CI use PostgreSQL
(see [ADR 0002](../adr/0002-postgresql-with-sqlite-for-local-development.md)). The base
settings (`farax/settings/base.py`) switch to PostgreSQL when `POSTGRES_DB` is set; the
other `POSTGRES_*` variables documented in `.env.example` have defaults. The production
settings require all of them. Django connects to PostgreSQL through psycopg.

## Settings

The base settings (`farax.settings`) need no configuration and are used for local
development and the tests. The production settings (`farax.settings.production`) extend
them, turn debug mode off, and read the secret key, allowed hosts, PostgreSQL
connection and SMTP email server from environment variables (see
[Production settings](index.md#production-settings)). They also add [WhiteNoise] so the
app serves its own static files.

## File Store

Raw Files are kept unchanged in the File Store, not in the database (see
[ADR 0003](../adr/0003-raw-files-in-file-store.md)). The File Store is the default
storage in Django's `STORAGES` setting: a `FileSystemStorage` rooted in the git-ignored
`media/` directory (`MEDIA_ROOT`), or in the directory set by `DJANGO_MEDIA_ROOT`. Docker
Compose keeps it on the named volume `media`. Code should save and read Raw Files through Django's
storage API (`django.core.files.storage.default_storage` or a model `FileField`), so the
File Store can later move to object storage by changing only the settings.

[Django]: https://www.djangoproject.com/
[WhiteNoise]: https://whitenoise.readthedocs.io/
