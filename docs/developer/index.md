# Developer Guide

!!! note
    This page is a stub. It will be expanded as the project develops.

This documentation is intended for both humans and AI assistants and should be kept in
sync with changes in the codebase.

The documentation is structured as a series of short concise files arranged in a
hierarchy. Cross-links and indexes should be actively maintained. If the documentation
contains inaccurate or out-of-date information update the docs.

## Setup

[Install uv], then install FaraX and its dependencies into a virtual environment and set
up the pre-commit git hooks:

```bash
uv sync --all-groups
uv run pre-commit install
```

Preface commands with `uv run` to use the virtual environment, or activate it with
`source .venv/bin/activate`.

## Running the app

With no configuration FaraX uses SQLite, stored in the git-ignored `db/` directory.

```bash
uv run python manage.py migrate          # create or update the database tables
uv run python manage.py createsuperuser  # create an account for the Django admin
uv run python manage.py runserver        # serve the app at http://127.0.0.1:8000/
```

The Django admin is at `http://127.0.0.1:8000/admin/`. After changing models, generate
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

### Schema uploads

`DJANGO_SCHEMA_UPLOAD_MAX_BYTES` sets the largest schema file, in bytes, that an
administrator can upload to register a schema.

### Running with Docker Compose

Docker Compose runs the full base stack, the web app and PostgreSQL 18, with nothing
installed but Docker. `docker-compose.yml` defines two services:

- `web`, built from the `Dockerfile`, applies any pending migrations and then runs
  Django's development server at `http://127.0.0.1:8000/`. The repository is mounted
  read-only into the container, so the server reloads when you edit the source code but
  the container can't change it. Rebuild the image (`docker compose build`) only after
  changing dependencies.
- `postgres` runs PostgreSQL 18.

Both read the git-ignored `.env` file, created from `.env.example`. The database and the
File Store are kept on the named volumes `postgres` and `media`, so their contents
survive `docker compose down`. Use `docker compose down -v` to delete them.

```bash
cp .env.example .env     # once; the example values work as they are
docker compose up        # start the stack (add -d to run it in the background)
```

Migrations are applied each time the `web` service starts; restart it
(`docker compose restart web`) to apply migrations added while it is running. In
another terminal, create a superuser, then log in at `http://127.0.0.1:8000/admin/`:

```bash
docker compose exec web python manage.py createsuperuser
```

Other management commands that don't write to the source tree run the same way with
`docker compose exec web python manage.py <command>`. The image installs the runtime
dependencies and FaraX itself from `uv.lock` into `/opt/venv`, without editable mode and
without the development tools, so run the tests and linters on the host with uv.

The container has no `.git` directory, so `setuptools-scm` can't work out the version
and `farax.__version__` is `0.0.0` in the image. Pass the real version when building if
it matters:

```bash
docker compose build --build-arg FARAX_VERSION=$(git describe --tags)
```

The container runs as the unprivileged `nobody` user and never creates files in the
mounted source tree: the mount is read-only and Python doesn't write bytecode
(`PYTHONDONTWRITEBYTECODE`). Only the File Store volume is writable. Run commands that
write to the source tree, such as `makemigrations`, on the host with uv:

```bash
uv run python manage.py makemigrations
```

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

Email is sent over SMTP. These variables are optional, and empty values count as unset:

| Variable | Purpose | Default |
| --- | --- | --- |
| `DJANGO_EMAIL_HOST` | Address of the SMTP server. | `localhost` |
| `DJANGO_EMAIL_PORT` | Port of the SMTP server, a whole number. | 587 with TLS, otherwise 25 |
| `DJANGO_EMAIL_HOST_USER` | User to log in to the SMTP server as. | don't log in |
| `DJANGO_EMAIL_HOST_PASSWORD` | Password of the SMTP user. | don't log in |
| `DJANGO_EMAIL_USE_TLS` | `true` to use STARTTLS, `false` not to (`1`/`0`, `yes`/`no` and `on`/`off` also work). | `false` |

Django refuses to start if `DJANGO_EMAIL_PORT` or `DJANGO_EMAIL_USE_TLS` can't be
understood. Django 6.1 configures email through the `MAILERS` setting rather than the
deprecated `EMAIL_*` settings, so the production settings pass these values to the SMTP
backend as `MAILERS["default"]["OPTIONS"]`. The base settings print emails to the
console instead.

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
directory unless `DJANGO_MEDIA_ROOT` points somewhere else.

## Common tasks

```bash
uv run pytest                    # run the tests
uv run mypy .                    # type check
uv run pre-commit run --all-files  # lint and format
uv run mkdocs serve              # preview the documentation
```

## Contents

- [Architecture](architecture.md): FaraX-specific design of the Django project.
- [Conventions](conventions.md): rules for Django code, settings, tests and Docker.
- [Contributing](contributing.md): the contribution workflow.
- [Schema registry design](schema-registry.md): the proposed approach for registering JSON Schemas.
- Architecture decision records:
    - [0001 Single repository for all components](../adr/0001-single-repository.md)
    - [0002 PostgreSQL in production, SQLite tolerated for local development](../adr/0002-postgresql-with-sqlite-for-local-development.md)
    - [0003 Raw Files are kept in a File Store, not the database](../adr/0003-raw-files-in-file-store.md)
    - [0004 Registered Schema definitions are immutable (proposed)](../adr/0004-immutable-registered-schemas.md)

[WhiteNoise]: https://whitenoise.readthedocs.io/
[Install uv]: https://docs.astral.sh/uv/getting-started/installation/
