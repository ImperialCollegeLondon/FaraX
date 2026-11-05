# Copilot Instructions

FaraX is a Django web application (Python >=3.14), managed with [uv], for a data management platform for materials discovery. It is a single Django project at the repository root: `manage.py`, the project package `farax/` and a single app `main/`.

The developer documentation in `docs/developer/` is the reference for how the project works. Read it before changing Django code, settings, environment variables, the database, the File Store or Docker: `architecture.md` describes FaraX-specific design, `conventions.md` the rules for Django code, tests and Docker, and `index.md` how to run the app and its environment variables. Domain terms are defined in `GLOSSARY.md` and decisions recorded in `docs/adr/`.

## Build, test, lint

```bash
uv sync --all-groups                 # install everything (CI uses `uv sync`, docs use `--group doc`)
uv run pytest                        # full suite (coverage + doctests enabled via addopts)
uv run pytest tests/test_farax.py::test_version   # single test
uv run mypy .                        # type check
uv run ruff check --fix . && uv run ruff format .
uv run pre-commit run --all-files    # all linters
uv run mkdocs build --strict         # docs (needs the `doc` group)
```

Running the app, PostgreSQL and Docker Compose are covered in `docs/developer/index.md`.
CI (`.github/workflows/ci.yml`) runs `mypy .`, `pytest` (against a `postgres:18` service), and a strict mkdocs build.

## Conventions

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
  experts. We avoid complex architectures, convoluted abstractions and software
  engineering jargon.
- When reviewing, check changes against `docs/developer/conventions.md` as well as the
  rules here.

## Agent workflow

- Implement in feature branches off `main`, each in its own git worktree, keeping the
  developer's checkout untouched. Stage files by path (`git add <paths>`).
- Implement with lighter-weight models (not Opus). Review with a model from a different
  vendor to the implementer, e.g. review Anthropic models with OpenAI models.
- For a spec split into tickets: open a feature PR from the integration branch to `main`
  carrying the `Closes` keywords. Give each ticket its own PR against the integration
  branch, or against its blocker's branch while that blocker is unmerged (stacked PRs).
  The developer reviews and merges ticket PRs; merge directly rather than through a
  merge subagent.

[uv]: https://docs.astral.sh/uv
