# Changes for pueblo

## Unreleased
- Add a few testing helper utilities to `pueblo.testing`
- Fix dependencies for `test` extra by downgrading to `nbdime<4`
- Dependencies (extras): Remove "ngr", add "notebook", link "test" to "testing"
- ngr: Gradle test runner failed to invoke `./gradlew install` because such a
  target did not exist.
- ngr: Fix Gradle test runner by only conditionally invoking `gradle wrapper`
- ngr: Add capability to invoke projects using the `poethepoet` task runner
 
## 2023-11-06 v0.0.3
- ngr: Fix `contextlib.chdir` only available on Python 3.11 and newer

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
