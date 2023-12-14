# Changes for pueblo

## Unreleased
- ngr: Add capability to invoke Meltano projects

## 2023-12-05 v0.0.4
- Add a few testing helper utilities to `pueblo.testing`
- Fix dependencies for `test` extra by downgrading to `nbdime<4`
- Dependencies (extras): Remove "ngr", add "notebook", link "test" to "testing"
- ngr: Gradle test runner failed to invoke `./gradlew install` because such a
  target did not exist.
- ngr: Fix Gradle test runner by only conditionally invoking `gradle wrapper`
- ngr: Add capability to invoke projects using the `poethepoet` task runner
- Dependencies: Update to nbdime 4 and pytest-notebook 0.10
- Add `pueblo.io.to_io` utility function
- ngr: Improve .NET runner by accepting `--dotnet-version` command-line option
- ngr: Fix Gradle test runner by wiping existing Gradle wrappers, to accommodate
  for contemporary versions of Java
- Add support for Python 3.7
- Add `testbook` to `notebook` subsystem
- Add `pueblo.util.proc.process` utility. It is a wrapper around
  `subprocess.Popen` to also terminate child processes after exiting.
  Thanks, @pcattori.
 
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
