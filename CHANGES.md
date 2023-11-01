# Changes for pueblo

## Unreleased

## 2023-11-01 v0.0.2
- ngr: Use Makefile runner as fallback
- ngr: Add runner for Julia projects
- ngr: Improve runner for Python projects
  Also consider setup.py, setup.cfg, pyproject.toml, and poetry.lock.
- ngr: Add runner for Golang projects
- ngr: Add runner for Elixir projects
- ngr: Add runner for Haskell projects
- ngr: Fix Python runner about `error: Multiple top-level modules discovered in
  a flat-layout`
- ngr: Fix Python runner about `pytest --config-file=.`

## 2023-10-30 v0.0.1
- Add `pueblo.util.logging.setup_logging`, nomen est omen
- Add `pueblo.util.environ.getenvpass`, a wrapper around `os.environ`,
  `dotenv`, and `getpass`
- Add `pueblo.testing.notebook`, including a monkeypatch to `pytest-notebook`
- Add `CachedWebResource`, a wrapper around `requests-cache` and `langchain`
- Add `pueblo.ngr`, a versatile test suite runner
