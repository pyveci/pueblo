# Changes for pueblo

## Unreleased
- Testing: Fixed `ValueError: Invalid frequency: S. Failed to parse with
  error message: Did you mean s?`
- ngr: Updated to poethepoet 0.38 at `ngr-python-test-poethepoet`

## 2025-12-15 v0.0.13
- nlp: Switched from `langchain` to `langchain-core`
- Testing: Migrated from pytest's `LocalPath` to `pathlib.Path`

## 2025-11-05 v0.0.12
- ngr: Stopped overwriting existing Gradle wrapper. The `--gradle-wrapper`
  option can be used to optionally regenerate the Gradle wrapper now.
- ngr: Deprecated Python's `--accept-no-venv` option: The test runner
  should not apply any governance here.

## 2025-01-19 v0.0.11
- ngr: For invoking Elixir, use `mix test --trace`
- ngr: Added as dedicated install extra, `pip install pueblo[ngr]`
- Testing: Unlocked compatibility with pytest version 8
- SFA: Added a subsystem for loading single-file applications

## 2024-10-03 v0.0.10
- nlp: Updated dependencies langchain, langchain-text-splitters, unstructured
- CI: Verify compatibility with Python 3.13
- Testing: Add `pueblo.testing.notebook.{list_notebooks,generate_notebook_tests,run_notebook}`

## 2024-03-07 v0.0.9
- Testing: Add `pueblo.testing.notebook.{list_path,generate_tests}`

## 2024-02-10 v0.0.8
- ngr: Add capability to invoke Python's built-in `unittest`

## 2024-01-30 v0.0.7
- Testing: Add `pueblo.testing.pandas.{makeTimeDataFrame,makeMixedDataFrame}`.
  They have been removed from `pandas._testing` on behalf of pandas 2.2.0.

## 2024-01-19 v0.0.6
- Packaging: Fix `MANIFEST.in`

## 2024-01-19 v0.0.5
- Dependencies: Update to pytest-notebook >=0.10,
  lower versions are not compatible any longer
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
