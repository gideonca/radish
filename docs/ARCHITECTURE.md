# Radish Architecture Guide

This document describes the internal architecture of Radish, how services are initialized, and how commands are organized.

## Overview

Radish uses two key architectural patterns:

1. **Service Factory Pattern** - Centralized initialization of all services
2. **Command Module Organization** - Commands grouped by domain into focused modules

## Service Factory Pattern

The `ServiceFactory` class (`src/factory.py`) manages all application services as singletons. This approach has several benefits:

### Benefits

- **No import-time side effects** - Services are created on-demand, not when modules are imported
- **Easy testing** - Call `ServiceFactory.reset()` to clean up between tests
- **Explicit dependency order** - Clear initialization sequence with no implicit dependencies
- **Configuration flexibility** - Pass settings to `initialize()`

### Usage

#### Initialization

```python
from src.factory import ServiceFactory

# Initialize all services at startup
ServiceFactory.initialize(auto_backup_interval=300)
```

#### Accessing Services

```python
# Get the store
store = ServiceFactory.get_store()

# Get the command handler
command_handler = ServiceFactory.get_command_handler()

# Get other services
persistence = ServiceFactory.get_persistence()
event_handler = ServiceFactory.get_event_handler()
logging = ServiceFactory.get_logging_handler()
```

#### Testing

```python
def test_something():
    ServiceFactory.initialize()
    
    # Run your test
    store = ServiceFactory.get_store()
    store.set('key', 'value')
    
    # Clean up
    ServiceFactory.reset()
```

### Managed Services

| Service | Class | Purpose |
|---------|-------|---------|
| **Store** | `ExpiringStore` | Core key-value data store with TTL support |
| **Command Handler** | `CommandHandler` | Routes and executes commands |
| **Persistence** | `PersistenceHandler` | Manages automatic backups |
| **Event Handler** | `EventHandler` | Manages event system and responses |
| **Logging** | `LoggingHandler` | Handles all logging operations |

## Command Organization

Commands are organized into focused domain modules under `src/commands/`. This structure makes the codebase more maintainable and easier to extend.

### Module Structure

```
src/commands/
├── __init__.py                 # Package exports
├── base.py                     # Command decorator and CommandMixin
├── string_commands.py          # String key-value operations
├── list_commands.py            # List operations
├── cache_commands.py           # Named cache management
├── store_commands.py           # Store management
└── utility_commands.py         # Utilities and diagnostics
```

### Command Distribution

| Module | Commands | Count |
|--------|----------|-------|
| **StringCommands** | SET, GET, DEL, LPOP, EXPIRE | 5 |
| **ListCommands** | LPUSH, RPUSH | 2 |
| **CacheCommands** | CREATECACHE, DELETECACHE, LISTCACHES, CACHESET, CACHEGET, CACHEDEL, CACHEKEYS, CACHEGETALL | 8 |
| **StoreCommands** | CREATESTORE, DELETESTORE, LISTSTORES | 3 |
| **UtilityCommands** | PING, ECHO, INSPECT, HISTORY, REPLAY | 5 |
| **Total** | — | 23 |

### How CommandHandler Works

`CommandHandler` uses **multiple inheritance** to combine all command mixins:

```python
class CommandHandler(
    CommandMixin,                # Base mixin with _get_history()
    StringCommands,              # All string operations
    ListCommands,                # All list operations
    CacheCommands,               # All cache operations
    StoreCommands,               # All store operations
    UtilityCommands,             # All utilities
):
    def __init__(self, store):
        # Initialize dependencies
        self.store = store
        self.event_handler = EventHandler()
        self.validation_handler = ValidationHandler()
        
        # Auto-discover all command handlers
        self._handlers = {}
        for _, method in inspect.getmembers(self, predicate=inspect.ismethod):
            for cmd in getattr(method, '_commands', []):
                self._handlers[cmd] = method
```

The `@command(...)` decorator in `base.py` registers methods:

```python
from src.commands.base import command

class StringCommands:
    @command('SET')
    def _handle_set(self, args):
        key, value = args[0], args[1]
        self.store.set(key, value)
        return 'OK'
    
    @command('GET')
    def _handle_get(self, args):
        key = args[0]
        return str(self.store.get(key, 'NULL'))
```

The `@command('SET')` decorator adds a `_commands` attribute (`['SET']`) to the method. During `CommandHandler.__init__`, all methods with `_commands` are discovered and registered in `_handlers`.

## Core Service Details

### ExpiringStore

The data store at the heart of Radish:

- **Thread-safe** - Uses fine-grained locks for concurrent access
- **TTL support** - Keys can expire automatically
- **Named caches** - Organize data into isolated namespaces
- **Background cleanup** - Periodically removes expired keys
- **Various data types** - Stores strings, lists, dicts, and custom objects

### CommandHandler

Processes all incoming commands:

- **Validation** - Checks command syntax before execution
- **Preprocessing** - Handles special cases like SET with multi-word values
- **Command execution** - Routes to appropriate handler
- **History tracking** - Optional command history for replay
- **Error handling** - Catches and reports exceptions

### EventHandler

Manages event system:

- **Response formatting** - Converts handler results to network format
- **Error responses** - Formats error messages
- **Exit handling** - Manages client disconnection

### ValidationHandler

Validates commands:

- **Syntax checking** - Verifies command structure
- **Argument counting** - Ensures correct number of arguments
- **Extensible specs** - Command specifications in data structure

### PersistenceHandler

Manages automatic backups:

- **Background backups** - Periodic snapshots to disk
- **Graceful shutdown** - Final backup before exit
- **Restore capability** - Load from backup files

## Request Flow

When a client sends a command, it flows through the system like this:

```
Network Socket
    ↓
server.py: handle_client_connection()
    ↓
CommandHandler.handle_command()
    ├─→ Preprocess command parts
    ├─→ ValidationHandler.validate_command()
    ├─→ Lookup command handler
    ├─→ Execute handler (e.g., _handle_set)
    ├─→ Update command history
    └─→ EventHandler.handle_response()
    ↓
Network Socket (response sent back)
```

## Module Dependencies

```
server.py
  ├─→ factory.py
  │   ├─→ expiring_store.py
  │   ├─→ command_handler.py
  │   │   ├─→ commands/base.py (decorator)
  │   │   ├─→ commands/string_commands.py
  │   │   ├─→ commands/list_commands.py
  │   │   ├─→ commands/cache_commands.py
  │   │   ├─→ commands/store_commands.py
  │   │   ├─→ commands/utility_commands.py
  │   │   ├─→ validation_handler.py
  │   │   └─→ event_handler.py
  │   ├─→ persistence_handler.py
  │   ├─→ event_handler.py
  │   └─→ logging_handler.py
  └─→ http_server.py
```

## Design Principles

1. **Single Responsibility** - Each module has one clear purpose
2. **Loose Coupling** - Minimal dependencies between modules
3. **High Cohesion** - Related functionality grouped together
4. **Extensibility** - Easy to add commands and features
5. **Testability** - Can test components in isolation
6. **Pure Python** - No external dependencies beyond stdlib

## Performance Considerations

- **Thread-safe** - Fine-grained locking for concurrent access
- **Background cleanup** - TTL expiration doesn't block requests
- **Efficient lookup** - O(1) command handler lookup using dictionary
- **Memory efficient** - No unnecessary data duplication
- **Fast serialization** - Simple text protocol

## Future Enhancements

The current architecture enables:

1. **Plugin System** - Load custom command modules dynamically
2. **Configuration Layer** - Externalize settings to config files
3. **Metrics** - Track command execution times and success rates
4. **Clustering** - Multi-node deployment support
5. **Pub/Sub** - Publish-subscribe messaging system
6. **Transactions** - MULTI/EXEC command support

## Debugging Tips

### Viewing Registered Commands

```python
from src.factory import ServiceFactory
ServiceFactory.initialize()
handler = ServiceFactory.get_command_handler()
print(sorted(handler._handlers.keys()))
```

### Tracing Command Execution

Enable debug logging in `logging_handler.py` to see command flow.

### Testing Command Handlers

```python
from src.expiring_store import ExpiringStore
from src.command_handler import CommandHandler

store = ExpiringStore()
handler = CommandHandler(store)

responses = []
def send_response(msg):
    responses.append(msg)

handler.handle_command(['SET', 'key', 'value'], send_response)
print(responses)
```
