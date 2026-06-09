# Copilot Instructions for Radish

Radish is a pure-stdlib Python project that implements a Redis-like TCP server plus a thin HTTP wrapper. Prefer the source and tests over the prose docs when behavior matters.

## Commands

```bash
# Run the TCP server
python server.py

# Run the HTTP wrapper (expects the TCP server on 127.0.0.1:6379)
python http_server.py

# Full unit suite
python3 -m unittest discover -s tests/unit

# Run a single unit test
python3 -m unittest tests.unit.test_command_handler.TestCommandHandler.test_set_get

# Full integration unittest suite
python3 -m unittest discover -s tests/integration

# Run a single integration test
python3 -m unittest tests.integration.test_connection.TestConnection.test_ping_response

# Script-style integration smoke tests that are not normal unittest discovery targets
python3 tests/integration/test_persistence.py
python3 tests/integration/test_cachegetall.py
python3 tests/integration/test_event_handling.py
```

Integration tests expect a live Radish server on `localhost:6379`. The discovered unittest-based integration tests are guarded with `@unittest.skipUnless(...)`; some other files in `tests/integration/` are executable scripts instead of discovered `TestCase` modules.

## High-level architecture

- `server.py` is the TCP entry point. It creates module-level singletons for `ExpiringStore`, `PersistenceHandler`, `CommandHandler`, and `LoggingHandler`, then `start_server()` binds `127.0.0.1:6379` and spins one thread per client connection.
- The TCP request path is: socket receive -> `request.strip().split()` in `handle_client_connection()` -> `CommandHandler.handle_command()` -> `EventHandler.handle_response()` / `handle_error()`.
- `src/command_handler.py` owns command execution. Command handlers are registered with the `@command(...)` decorator and auto-discovered in `CommandHandler.__init__`; validation remains centralized in `src/validation_handler.py`.
- `src/expiring_store.py` is the actual runtime backing store for the TCP server. It combines default key/value storage, TTL expiration, and named-cache support in one object. Named caches are stored as dictionary values inside the same `ExpiringStore`, with helper methods like `create_cache()`, `cache_set()`, `cache_keys()`, and `cache_get_all()`.
- `http_server.py` is not a second datastore. It is a thin REST adapter that translates HTTP requests into raw Radish text commands and forwards them over a TCP socket to the server on port `6379`. Changes to command parsing usually affect both TCP and HTTP behavior.
- `src/cache_handler.py` is a richer standalone API with searching, stats, event hooks, and persistence-oriented helpers. Many unit tests target this layer directly, but it is not wired into `server.py` or `http_server.py`.
- Persistence and logging write outside the repo: backups go to `~/.radish/cache_backup`, logs go to `~/.radish/logs`. The server triggers a final backup during shutdown.

## Key conventions

- When adding or changing a TCP command, update both places:
  1. `ValidationHandler._command_specs` in `src/validation_handler.py`
  2. A `@command(...)`-decorated handler method in `src/command_handler.py`
- Command dispatch is discovery-based, not a manual command map. New handlers become active because `CommandHandler.__init__` inspects bound methods for the `_commands` attribute added by the decorator.
- The wire protocol is whitespace-tokenized. `server.py` splits incoming requests with `str.split()`, and `CommandHandler._preprocess_set_command()` only re-joins multi-token values for `SET`. Be careful when changing JSON or space-containing payload behavior, because `CACHESET` and HTTP endpoints ultimately depend on the same text protocol.
- Import side effects matter. `server.py` constructs the store, persistence handler, logging handler, and their background threads at module import time, not lazily inside `main()`.
- The repository currently has drift between some docs/tests and the live implementation. For behavior-sensitive work, confirm the exact code path you are editing instead of assuming README or guide examples are authoritative.
- Tests use the standard library `unittest` runner; there is no project-local build system or lint configuration to update alongside code changes.
