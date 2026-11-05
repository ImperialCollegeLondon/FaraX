# FaraX

A data management platform for synthesisability in data-driven materials discovery. It
ingests, validates, stores and visualises research data.

FaraX is a [Django] web application that uses [uv] for packaging and dependency
management. It was developed by the [Imperial College Research Software Engineering
Team].

## Quick start

With [uv installed][Download and install uv], run FaraX locally with SQLite and log in
at `http://127.0.0.1:8000/admin/`:

```bash
uv sync --all-groups
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Or, with only [Docker] installed, run FaraX with PostgreSQL:

```bash
cp .env.example .env
docker compose up
docker compose exec web python manage.py createsuperuser  # in another terminal
```

Run the tests with `uv run pytest`.

## Documentation

The [Developer Guide] covers setup, running FaraX against
PostgreSQL and with Docker Compose, production settings and environment variables, the
architecture and the project's conventions.

[Django]: https://www.djangoproject.com/
[Developer Guide]: https://github.com/ImperialCollegeLondon/FaraX/blob/main/docs/developer/index.md
[Docker]: https://docs.docker.com/get-started/get-docker/
[uv]: https://docs.astral.sh/uv
[Imperial College Research Software Engineering Team]: https://www.imperial.ac.uk/admin-services/ict/self-service/research-support/rcs/service-offering/research-software-engineering/
[Download and install uv]: https://docs.astral.sh/uv/getting-started/installation/
