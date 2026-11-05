# Developer Guide

!!! note
    This page is a stub. It will be expanded as the project develops.

This documentation is intended for both humans and AI assistants and should be kept in
sync with changes in the codebase.

The documentation is structured as a series of short concise files arranged in a
hierarchy. Cross-links and indexes should be actively maintained. If the documentation
contains inaccurate or out-of-date information update the docs.

## Setup

```bash
uv sync --all-groups
uv run pre-commit install
```

## Running the app

With no configuration FaraX uses SQLite, stored in the git-ignored `db/` directory.

```bash
uv run python manage.py migrate          # create or update the database tables
uv run python manage.py createsuperuser  # create an account for the Django admin
uv run python manage.py runserver        # serve the app at http://127.0.0.1:8000/
```

The Django admin is at <http://127.0.0.1:8000/admin/>. After changing models, generate
a migration with `uv run python manage.py makemigrations` and commit it.

### Running against PostgreSQL

Production and CI use PostgreSQL. To reproduce their behaviour locally, set the
`POSTGRES_*` environment variables listed in `.env.example`; setting `POSTGRES_DB`
switches from SQLite to PostgreSQL. FaraX doesn't load `.env` files itself, so export
the variables in your shell. For example, with a throwaway PostgreSQL container:

```bash
docker run -d --rm --name farax-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:18
export POSTGRES_DB=postgres POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres
uv run python manage.py migrate
uv run pytest                     # creates and drops a separate test_postgres database
docker stop farax-postgres
```

Treat PostgreSQL results as authoritative: some behaviour differs silently on SQLite.

## Production settings

Production deployments use the production settings, which extend the base settings:

```bash
export DJANGO_SETTINGS_MODULE=farax.settings.production
```

Debug mode is always off. The following environment variables are required, and Django
refuses to start if any of them is missing (see also `.env.example`):

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django's secret key; a long random string kept out of git. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names the site is served from. |
| `POSTGRES_DB` | Name of the PostgreSQL database. |
| `POSTGRES_USER` | PostgreSQL user to connect as. |
| `POSTGRES_PASSWORD` | Password of the PostgreSQL user. |
| `POSTGRES_HOST` | Address of the PostgreSQL server. |
| `POSTGRES_PORT` | Port of the PostgreSQL server. |

The production settings expect a reverse proxy in front of the app that terminates HTTPS
and sets the `X-Forwarded-Proto` header. Requests over plain HTTP are redirected to
HTTPS.

Static files, such as the Django admin's stylesheets, are served by the app itself
through [WhiteNoise]. Collect them into the git-ignored `staticfiles/` directory before
starting the app:

```bash
uv run python manage.py collectstatic --no-input
uv run python manage.py check --deploy  # Django's deployment checks
```

Raw Files are kept in the File Store (see
[ADR 0003](../adr/0003-raw-files-in-file-store.md)), which is the git-ignored `media/`
directory in every configuration.

## Common tasks

```bash
uv run pytest                    # run the tests
uv run mypy .                    # type check
uv run pre-commit run --all-files  # lint and format
uv run mkdocs serve              # preview the documentation
```

## Contents

- [Architecture](architecture.md): layout of the Django project and its app.
- [Contributing](contributing.md): the contribution workflow.
- Architecture decision records:
    - [0001 Single repository for all components](../adr/0001-single-repository.md)
    - [0002 PostgreSQL in production, SQLite tolerated for local development](../adr/0002-postgresql-with-sqlite-for-local-development.md)
    - [0003 Raw Files are kept in a File Store, not the database](../adr/0003-raw-files-in-file-store.md)

[WhiteNoise]: https://whitenoise.readthedocs.io/
