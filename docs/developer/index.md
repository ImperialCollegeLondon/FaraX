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

## Common tasks

```bash
uv run pytest                    # run the tests
uv run mypy .                    # type check
uv run pre-commit run --all-files  # lint and format
uv run mkdocs serve              # preview the documentation
```

## Contents

- [Architecture](architecture.md): structure of the `farax` package.
- [Contributing](contributing.md): the contribution workflow.
- Architecture decision records:
    - [0001 Single repository for all components](../adr/0001-single-repository.md)
    - [0002 PostgreSQL in production, SQLite tolerated for local development](../adr/0002-postgresql-with-sqlite-for-local-development.md)
    - [0003 Raw Files are kept in a File Store, not the database](../adr/0003-raw-files-in-file-store.md)
