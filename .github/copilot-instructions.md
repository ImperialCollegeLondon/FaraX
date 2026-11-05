# Copilot Instructions

FaraX is a small Python (>=3.14) package scaffold, managed with [uv], for a data management platform for materials discovery. The package lives in `farax/` (entry point `farax/__main__.py`); the version is derived from git tags via `setuptools-scm`, so `farax.__version__` only exists when the package is installed in the environment.

## Build, test, lint

```bash
uv sync --all-groups                 # install everything (CI uses `uv sync`, docs use `--group doc`)
uv run python -m farax               # run the app
uv run pytest                        # full suite (coverage + doctests enabled via addopts)
uv run pytest tests/test_farax.py::test_version   # single test
uv run mypy .                        # type check
uv run ruff check --fix . && uv run ruff format .
uv run pre-commit run --all-files    # all linters
uv run mkdocs build --strict         # docs (needs the `doc` group)
```

CI (`.github/workflows/ci.yml`) runs `mypy .`, `pytest`, and a strict mkdocs build.

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
  executed (`farax/__main__.py` and `docs/` are ignored).
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
