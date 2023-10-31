# Changes for pueblo

## Unreleased
- ngr: Use Makefile runner as fallback

## 2023-10-30 v0.0.1
- Add `pueblo.util.logging.setup_logging`, nomen est omen
- Add `pueblo.util.environ.getenvpass`, a wrapper around `os.environ`,
  `dotenv`, and `getpass`
- Add `pueblo.testing.notebook`, including a monkeypatch to `pytest-notebook`
- Add `CachedWebResource`, a wrapper around `requests-cache` and `langchain`
- Add `pueblo.ngr`, a versatile test suite runner
