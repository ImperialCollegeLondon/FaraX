# FaraX

A data management platform for systhesisability in data-driven materials discovery.

FaraX is a [Django] web application that uses [uv] for packaging and dependency
management.
It provides [`pre-commit`][pre-commit] hooks for various linters
and formatters and automated tests using [`pytest`][pytest] and [GitHub Actions].
Pre-commit hooks are automatically kept updated with a dedicated GitHub Action, this can
be removed and replaced with [pre-commit.ci] if using a public repo. The package version
is dynamically generated from the most recent git tag using
[`setuptools-scm`][setuptools-scm].

It was developed by the [Imperial College Research Software Engineering Team].

## Usage

To get started:

1. [Download and install uv] following the instructions for your OS.
1. Activate a git repository (required for `pre-commit` and the package versioning with
    `setuptools-scm`):

    ```bash
    git init
    ```

1. Install the package and dependencies and set up the virtual environment:

    ```bash
    uv sync --all-groups
    ```

1. Activate the virtual environment, or just preface your commands with `uv run` to use
    the virtual environment (see [uv activate] for more info):

    ```bash
    source .venv/bin/activate
    <command>
    ```

    or

    ```bash
    uv run <command>
    ```

1. Install the pre-commit git hooks:

    ```bash
    uv run pre-commit install
    ```

1. Update the pre-commit hooks

    ```bash
    uv run pre-commit autoupdate
    ```

1. Create the database tables. With no configuration, data is stored in SQLite in the
    git-ignored `db/` directory:

    ```bash
    uv run python manage.py migrate
    ```

    To use PostgreSQL instead, set the `POSTGRES_*` environment variables documented in
    `.env.example` (see the developer guide).

1. Create a superuser account to log in to the Django admin:

    ```bash
    uv run python manage.py createsuperuser
    ```

1. Run the development server and log in at `http://127.0.0.1:8000/admin/`:

    ```bash
    uv run python manage.py runserver
    ```

1. Run the tests:

    ```bash
    uv run pytest
    ```

1. Create an initial commit (it's possible there might be some failures in pre-commit):

    ```bash
    git add .
    git commit -m "Initial commit"
    ```

## Running with Docker Compose

With only [Docker] installed, you can run FaraX with PostgreSQL using Docker Compose.
Source code changes reload the development server automatically, and the database and
File Store are kept on named volumes.

1. Create the git-ignored `.env` file. The example values work as they are:

    ```bash
    cp .env.example .env
    ```

1. Start the web app and PostgreSQL:

    ```bash
    docker compose up
    ```

1. In another terminal, create the database tables and a superuser:

    ```bash
    docker compose exec web python manage.py migrate
    docker compose exec web python manage.py createsuperuser
    ```

1. Log in at `http://127.0.0.1:8000/admin/`.

1. Stop the stack with `docker compose down`. Add `-v` to also delete the database and
    File Store volumes.

See the developer guide for more details.

## Updating Dependencies

Use the commands `uv add <package>` and `uv remove <package>` to add or remove dependencies.

- Use the optional flag `--dev` to add/remove development dependencies.
- Include the optional flag `--group <group-name>` to add/remove dependencies from specific groups.
- These will automatically update the `pyproject.toml` file.

For further information, see the [uv] docs for managing dependencies.

[Django]: https://www.djangoproject.com/
[Docker]: https://docs.docker.com/get-started/get-docker/
[uv]: https://docs.astral.sh/uv
[pre-commit]: https://pre-commit.com/
[pytest]: https://pytest.org/
[GitHub Actions]: https://github.com/features/actions
[pre-commit.ci]: https://pre-commit.ci
[setuptools-scm]: https://setuptools-scm.readthedocs.io/en/latest/
[Imperial College Research Software Engineering Team]: https://www.imperial.ac.uk/admin-services/ict/self-service/research-support/rcs/service-offering/research-software-engineering/
[Download and install uv]: https://docs.astral.sh/uv/getting-started/installation/
[uv activate]: https://docs.astral.sh/uv/pip/environments/
