# Radish

A lightweight Redis-like in-memory data store implementation in Python. Radish provides a thread-safe key-value store with automatic key expiration and a Redis-compatible command interface.

## Features

- **In-memory key-value store** - Fast data access with automatic expiration (TTL)
- **Named caches** - Organize data into isolated namespaces
- **JSON support** - Store and retrieve JSON objects with spaces preserved
- **Flexible backups** - Manual and automatic timestamped JSON backups to `~/.radish/cache_backup` (auto-backup disabled by default for memory efficiency)
- **Thread-safe operations** - Concurrent client support with fine-grained locking
- **Event system** - Monitor and react to cache operations (SET, DELETE, CREATE_CACHE, DELETE_CACHE, CLEAR)
- **Comprehensive logging** - Commands, responses, expirations, and server output with daily rotation
  - `radish_YYYY-MM-DD.log` - All commands, responses, errors, and expirations
  - `server_YYYY-MM-DD.log` - Server startup, shutdown, and connection events
- **Redis-like commands** - Familiar interface for Redis users
- **HTTP API** - REST access without external dependencies
- **List operations** - LPUSH, RPUSH, LPOP support
- **Memory efficient** - Disabled auto-backup and event tracking by default for minimal overhead
- **No dependencies** - Pure Python using only the standard library

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete guide to using Radish with examples and best practices
- **[Named Cache Guide](docs/NAMED_CACHE_GUIDE.md)** - Comprehensive guide to using named caches for organizing data
- **[Persistence Guide](docs/PERSISTENCE_GUIDE.md)** - Automatic backups, restore, and recovery procedures
- **[HTTP Server Guide](docs/HTTP_SERVER_GUIDE.md)** - Complete HTTP API documentation with examples
- **[Architecture Guide](docs/ARCHITECTURE.md)** - Detailed architecture, service factory, and command organization
- **[Extending Radish](docs/EXTENDING.md)** - How to add custom commands and extend the system
- **[Project Roadmap](docs/TODO.md)** - Planned features and development tasks

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/gideonca/radish.git
cd radish
```

2. Start the server:
```bash
python server.py
```

3. Connect using telnet:
```bash
telnet localhost 6379
```

### Basic Usage

```
> PING
PONG

> SET mykey "Hello World"
OK

> GET mykey
Hello World

> SET user {\"name\": \"Alice\", \"age\": 30}
OK

> GET user
{\"name\": \"Alice\", \"age\": 30}

> CREATECACHE sessions
OK

> CACHESET sessions session:123 {\"user_id\": 1, \"login\": \"2025-01-15T10:00:00\"}
OK

> CACHEGET sessions session:123
{\"user_id\": 1, \"login\": \"2025-01-15T10:00:00\"}

> EXPIRE mykey 60
OK

> EXIT
Goodbye!
```

For detailed usage instructions, see the **[User Guide](docs/USER_GUIDE.md)**.

### HTTP API

Start the HTTP server for REST API access:

```bash
python http_server.py
```

See the **[HTTP Server Guide](docs/HTTP_SERVER_GUIDE.md)** for complete API documentation.

## Command Overview

### Basic Commands
- `PING`, `SET`, `GET`, `DEL`, `EXPIRE`, `INSPECT`
- JSON support with spaces preserved in all commands

### List Operations
- `LPUSH`, `RPUSH`, `LPOP`

### Named Caches
- `CREATECACHE`, `DELETECACHE`, `LISTCACHES`
- `CACHESET`, `CACHEGET`, `CACHEDEL`, `CACHEKEYS`, `CACHEGETALL`
- JSON support with full value preservation

### Advanced Features
- `CREATESTORE`, `DELETESTORE`, `LISTSTORES` (Expiring stores)

For complete command reference and examples, see the **[User Guide](docs/USER_GUIDE.md)**.

## Development

Run the unit test suite:
```bash
python3 -m unittest discover -s tests/unit
```

Run integration tests (requires a running server):
```bash
python3 -m unittest discover -s tests/integration
```
```

## Implementation Details

### Architecture

Radish is built on a robust, modular architecture with clear separation of concerns. The codebase follows a plugin-inspired design with organized command modules and a factory pattern for service initialization.

#### Service Factory Pattern
The `ServiceFactory` class (`src/factory.py`) manages all service singletons with explicit initialization:

- **No import-time side effects** - Services are created on-demand when `ServiceFactory.initialize()` is called
- **Easy testing** - Call `ServiceFactory.reset()` between tests
- **Clear dependency order** - Initialization happens in a controlled sequence

Managed services:
- `ExpiringStore` - Core data store with TTL support
- `CommandHandler` - Command routing and execution
- `PersistenceHandler` - Automatic backups
- `EventHandler` - Event system
- `LoggingHandler` - Logging system

#### Command Module Organization
Commands are organized into logical domain modules for better maintainability:

- **String Commands** (`src/commands/string_commands.py`)
  - SET, GET, DEL, LPOP, EXPIRE
  
- **List Commands** (`src/commands/list_commands.py`)
  - LPUSH, RPUSH
  
- **Cache Commands** (`src/commands/cache_commands.py`)
  - CREATECACHE, DELETECACHE, LISTCACHES
  - CACHESET, CACHEGET, CACHEDEL, CACHEKEYS, CACHEGETALL
  
- **Store Commands** (`src/commands/store_commands.py`)
  - CREATESTORE, DELETESTORE, LISTSTORES
  
- **Utility Commands** (`src/commands/utility_commands.py`)
  - PING, ECHO, INSPECT, HISTORY, REPLAY

#### Core Layers

- **Data Store** (`src/expiring_store.py`)
  - TTL-based key expiration
  - Automatic background cleanup
  - Thread-safe value storage
  - Named cache support

- **Validation Layer** (`src/validation_handler.py`)
  - Registry-based command validation
  - Argument count and type checking
  - Extensible command specification system

- **Cache Management** (`src/cache_handler.py`)
  - Event-driven architecture
  - Comprehensive event system
  - Support for multiple cache instances

- **Event System** (`src/event_handler.py`)
  - Event-driven architecture for extensibility
  - Monitor and react to cache operations

### Technical Features

- Written in pure Python with no external dependencies
- Uses threading for concurrent client handling
- Thread-safe operations using fine-grained locks
- Event-driven architecture for extensibility
- Redis-compatible network protocol
- Automatic background maintenance tasks

## Project Structure

```
radish/
├── server.py                          # Main server entry point
├── http_server.py                     # HTTP API server (port 8000)
├── src/
│   ├── factory.py                     # Service factory for initialization
│   ├── validation_handler.py          # Command validation and registry
│   ├── command_handler.py             # Command dispatcher (uses command mixins)
│   ├── cache_handler.py               # Cache management and events
│   ├── expiring_store.py              # Key-value store with TTL and named caches
│   ├── event_handler.py               # Event system
│   ├── logging_handler.py             # Logging
│   ├── persistence_handler.py         # Data persistence
│   ├── stats_handler.py               # Statistics tracking
│   └── commands/                      # Organized command modules
│       ├── __init__.py                # Package exports
│       ├── base.py                    # Command decorator and mixins
│       ├── string_commands.py         # String operations (SET, GET, DEL, EXPIRE, LPOP)
│       ├── list_commands.py           # List operations (LPUSH, RPUSH)
│       ├── cache_commands.py          # Cache management (CREATECACHE, CACHESET, etc.)
│       ├── store_commands.py          # Store management (CREATESTORE, DELETESTORE, LISTSTORES)
│       └── utility_commands.py        # Utilities (PING, ECHO, INSPECT, HISTORY, REPLAY)
├── tests/
│   ├── unit/
│   │   ├── test_cache_handler.py      # Cache handler tests
│   │   ├── test_command_handler.py    # Command handler tests
│   │   ├── test_enhanced_cache_handler.py
│   │   ├── test_enhanced_features.py
│   │   ├── test_expiration_manager.py # TTL and expiration tests
│   │   └── test_validation_handler.py # Validation system tests
│   └── integration/
│       ├── test_connection.py         # TCP connectivity tests
│       ├── test_server_connection.py  # Server PING integration test
│       ├── test_cachegetall.py        # CACHEGETALL command test
│       ├── test_event_handling.py     # Event system integration test
│       └── test_persistence.py        # Backup/restore integration test
├── examples/
│   ├── event_handling_example.py      # Event system example
│   ├── http_client.py                 # HTTP API client example
│   └── named_cache.py                 # Named cache usage example
├── scripts/
│   ├── test_commands.sh               # Shell test for basic commands
│   ├── test_named_cache.sh            # Shell test for named caches
│   └── test_http.sh                   # Shell test for HTTP API
├── docs/
│   ├── USER_GUIDE.md                  # Complete usage guide
│   ├── NAMED_CACHE_GUIDE.md           # Named cache system guide
│   ├── PERSISTENCE_GUIDE.md           # Backup and restore guide
│   ├── HTTP_SERVER_GUIDE.md           # HTTP API documentation
│   ├── ARCHITECTURE.md                # Detailed architecture documentation
│   ├── EXTENDING.md                   # Guide to extending Radish with custom commands
│   └── TODO.md                        # Project roadmap and tasks
├── README.md                          # Project documentation
└── MITLicense.txt                     # License file
```

## Use Cases

1. **Development and Testing**
   - Local Redis replacement for development
   - Testing Redis-dependent applications
   - Learning Redis commands and behavior

2. **Educational**
   - Understanding key-value stores
   - Learning about concurrent programming
   - Studying Redis internals

3. **Prototyping**
   - Quick proof-of-concepts
   - System architecture exploration
   - Simple caching implementations