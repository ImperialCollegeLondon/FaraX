# Copilot Instructions

FaraX is a Django web application (Python >=3.14), managed with [uv], for a data management platform for materials discovery. It is a single Django project at the repository root, generated with `django-admin`: `manage.py`, the project package `farax/` (settings, root URLs, ASGI/WSGI) and a single app `main/` (models, admin, migrations). The version is derived from git tags via `setuptools-scm`, so `farax.__version__` only exists when the package is installed in the environment. See `docs/developer/architecture.md` for the layout.

## Build, test, lint

```bash
uv sync --all-groups                 # install everything (CI uses `uv sync`, docs use `--group doc`)
uv run python manage.py migrate      # create/update the local SQLite database in db/
uv run python manage.py createsuperuser  # account for the admin at /admin/
uv run python manage.py runserver    # run the app (no configuration needed)
uv run python manage.py makemigrations   # after changing models; commit the migration
uv run pytest                        # full suite (coverage + doctests enabled via addopts)
uv run pytest tests/test_farax.py::test_version   # single test
uv run mypy .                        # type check
uv run ruff check --fix . && uv run ruff format .
uv run pre-commit run --all-files    # all linters
uv run mkdocs build --strict         # docs (needs the `doc` group)
docker compose up                    # web + postgres:18 stack, runs migrations (needs `.env` from `.env.example`)
```

CI (`.github/workflows/ci.yml`) runs `mypy .`, `pytest` (against a `postgres:18` service), and a strict mkdocs build.

## Conventions

- **Django**: `main.User` (subclass of `AbstractUser`) is the auth user model; refer to
  it via `get_user_model()` or `settings.AUTH_USER_MODEL`. mypy uses the django-stubs
  plugin and pytest uses pytest-django (settings `farax.settings`); prefer testing
  through the Django test client (`client`, `admin_client`, `django_user_model`
  fixtures). Generated migrations are excluded from ruff and coverage. New apps or
  packages must be added to `[tool.setuptools] packages` and the pytest `--cov` targets.
  The pre-commit mypy hook runs in its own environment, so packages needed for type
  checking must also be listed in its `additional_dependencies`.
- **Settings**: `farax/settings/` is a package. `farax.settings` loads the base
  settings (`base.py`, no configuration needed); `farax.settings.production` extends
  them and requires `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` and the `POSTGRES_*`
  variables. Tests of the production settings run Django in a subprocess (see
  `tests/test_production_settings.py`) so they don't affect the rest of the session.
  Document new environment variables in `docs/developer/index.md` and `.env.example`.
- **File Store**: Raw Files are kept unchanged in the File Store, the default storage
  in `STORAGES` (git-ignored `media/`). Access it through Django's storage API, never
  by file paths, and never store Raw Files in the database.
- **Database**: PostgreSQL is the production database and CI runs the tests against it
  only. SQLite (in git-ignored `db/`) is tolerated for local development only and is
  used when `POSTGRES_DB` is unset; the `POSTGRES_*` variables are documented in
  `.env.example` (there is no dotenv dependency; `.env` is git-ignored and loaded only
  by Docker Compose). Don't add
  SQLite-specific code paths or skip tests for SQLite: if a PostgreSQL-only feature is
  needed, drop SQLite support rather than work around it.
- **Docker**: `Dockerfile` and `docker-compose.yml` are for development only (production
  Compose waits for the hosting target). The image installs runtime dependencies from
  `uv.lock` without editable mode into `/opt/venv`; Compose mounts the repository
  read-only at `/app` and keeps PostgreSQL data and the File Store
  (`DJANGO_MEDIA_ROOT`) on named volumes. Files needed in the image must be allowed in the `.dockerignore` allowlist.
- **Strict typing**: mypy forbids explicit `Any`, bare generics, and untyped defs (tests
  are exempt from the untyped-defs rule only). Instead of reaching for any `Any`
  consider `object` as an alternative. Whilst the default settings are strict, it may be
  appropriate to loosen them in places or use targeted suppression via comment. Doing
  this should be a deliberate decision where it simplifies code or in situations where
  type safety doesn't add much value. If disabling, this should be flagged to the user.
- **Docstrings**: ruff enforces pydocstyle with the **Google** convention on all
  modules, classes and functions, including `__init__.py` and new modules (only `tests/`
  is exempt from D100/D104).
- **Doctests run**: pytest uses `--doctest-modules`, so examples in docstrings are
  executed (`docs/` and `farax/settings/production.py` are ignored).
- **Docs**: API reference pages are generated from docstrings by `docs/gen_ref_nav.py`
  (mkdocs-gen-files + mkdocstrings), so docstrings are user-facing.
- Markdown must pass markdownlint (`.markdownlint.yaml`); spelling checked by codespell
  (allowlist in `.codespell_ignore.txt`). Add entries as appropriate.
- Manage dependencies with `uv add` / `uv remove` (`--dev` or `--group <name>`) rather
  than editing `pyproject.toml` by hand; `uv.lock` is committed.
- When implementing changes also update relevant documentation or agent instructions. If
  you are reviewing changes this is important to check.
- The project directory may also contain an AGENTS.local.md. The file is git ignored and
  provides developer preferences for the current session.
- This project is a collaboration between research software engineers and domain
  experts. Our approach combines software engineering best practices and domain
  expertise. Correctness and reproducibility are key concerns. We avoid complex
  architectures, convoluted abstractions and software engineering jargon.
- Further information about the codebase can be found in the developer documentation -
  `docs/developers.md`.
- Unless stated otherwise implementation should be carried out in feature branches off
  of `main`.

[uv]: https://docs.astral.sh/uv
