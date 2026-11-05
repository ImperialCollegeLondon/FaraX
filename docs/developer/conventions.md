# Conventions

Project-specific rules for working on FaraX's Django code. The general coding standards
(typing, docstrings, linting) are in `.github/copilot-instructions.md`.

## Django code

- Refer to the user model through `django.contrib.auth.get_user_model()` or
  `settings.AUTH_USER_MODEL`, never Django's built-in `User` (see
  [User model](architecture.md#user-model)).
- Save and read Raw Files through Django's storage API, never by file paths, and never
  store Raw Files in the database (see [File Store](architecture.md#file-store)).
- Don't add SQLite-specific code paths or skip tests on SQLite. If a PostgreSQL-only
  feature is needed, drop SQLite support instead (see
  [Database](architecture.md#database)).
- After changing models, generate a migration on the host with
  `uv run python manage.py makemigrations` and commit it. Generated migrations are
  excluded from ruff and coverage.
- Add new apps or packages to `[tool.setuptools] packages` in `pyproject.toml`, so the
  Docker image (which installs FaraX without editable mode) includes them, and to the
  pytest `--cov` targets.

## Settings and environment variables

`farax/settings/` is a package. `farax.settings` loads the base settings (`base.py`),
which need no configuration; `farax.settings.production` extends them (see
[Production settings](index.md#production-settings)). FaraX has no dotenv dependency:
the git-ignored `.env` file is loaded only by Docker Compose.

Document every new environment variable in `.env.example` and in the
[Developer Guide](index.md), and, for production variables, in the docstring of
`farax/settings/production.py`.

## Tests and type checking

- pytest uses pytest-django with the `farax.settings` settings. Prefer testing through
  the Django test client and the `client`, `admin_client` and `django_user_model`
  fixtures. Test behaviour, not settings values or the framework itself.
- Tests of the production settings run Django in a subprocess (see
  `tests/test_production_settings.py`), so they don't affect the rest of the session.
- mypy uses the django-stubs plugin. The pre-commit mypy hook runs in its own
  environment, so packages needed for type checking must also be listed in its
  `additional_dependencies` in `.pre-commit-config.yaml`.

## Docker

`Dockerfile` and `docker-compose.yml` are for development only; production Compose waits
until the hosting target is decided. Name Compose files `docker-compose.yml` (a
pre-commit hook checks this). Containers run as `nobody` and mount the source tree
read-only, so they never create files in it (see
[Running with Docker Compose](index.md#running-with-docker-compose)). Files needed in the
image must be allowed in the `.dockerignore` allowlist.

## Documentation

Each fact has one home. The README is a short overview and quick start that links to the
Developer Guide; detail lives in `docs/developer/`, and other pages link to it rather than
repeating it.

## Dependencies

Add or remove dependencies with `uv add <package>` and `uv remove <package>` rather than
editing `pyproject.toml` by hand. Use `--dev` for development tools and
`--group <name>` for a specific group (for example `--group doc`). Commit the updated
`uv.lock`.
