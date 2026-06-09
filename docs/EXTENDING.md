# Extending Radish

This guide shows how to add custom commands to Radish and extend the system with new functionality.

## Adding a New Command

The process for adding a new command is simple:

1. Choose which module your command belongs to
2. Add a handler method with the `@command(...)` decorator
3. Update validation specs (if needed)
4. Test your command

### Example: Adding a GETRANGE Command

Let's add a command that returns a substring of a value.

#### Step 1: Choose the Module

Since `GETRANGE` operates on strings, it belongs in `src/commands/string_commands.py`.

#### Step 2: Add the Handler

Open `src/commands/string_commands.py` and add:

```python
@command('GETRANGE')
def _handle_getrange(self, args: List[str]) -> str:
    """
    Handle GETRANGE command.
    
    Args:
        args: [key, start, end] where start and end are 0-based indices
        
    Returns:
        str: The substring, or 'NULL' if key doesn't exist
    """
    key = args[0]
    start = int(args[1])
    end = int(args[2])
    
    value = str(self.store.get(key, 'NULL'))
    if value == 'NULL':
        return 'NULL'
    
    return value[start:end+1]
```

#### Step 3: Update Validation (Optional)

If you need to validate this command, open `src/validation_handler.py` and add to `_command_specs`:

```python
'GETRANGE': {
    'min_args': 3,
    'max_args': 3,
    'description': 'Get substring of a value'
}
```

#### Step 4: Test It

```bash
# Start the server
python server.py

# In another terminal, test:
echo -e "SET mykey 'Hello World'\nGETRANGE mykey 0 4\nGETRANGE mykey 6 10" | nc localhost 6379
```

Or write a unit test:

```python
import unittest
from src.expiring_store import ExpiringStore
from src.command_handler import CommandHandler

class TestGetRange(unittest.TestCase):
    def setUp(self):
        self.store = ExpiringStore()
        self.handler = CommandHandler(self.store)
        self.responses = []
        
    def send_response(self, response):
        self.responses.append(response.decode('utf-8'))
        
    def test_getrange(self):
        self.handler.handle_command(['SET', 'mykey', 'Hello World'], self.send_response)
        self.handler.handle_command(['GETRANGE', 'mykey', '0', '4'], self.send_response)
        self.assertEqual(self.responses[-1].strip(), 'Hello')
```

## Creating a New Command Module

If you have many related commands that don't fit existing modules, create a new module.

### Example: Adding Analytics Commands

Create `src/commands/analytics_commands.py`:

```python
"""Analytics and statistics commands."""

from typing import List
from .base import command


class AnalyticsCommands:
    """Analytics command handlers."""
    
    @command('STATS')
    def _handle_stats(self, args: List[str]) -> str:
        """
        Return statistics about the store.
        
        Returns:
            str: Formatted statistics
        """
        keys = self.store.keys()
        total_memory = sum(len(str(self.store.get(k))) for k in keys)
        
        result = [
            f'Total keys: {len(keys)}',
            f'Total memory (approx): {total_memory} bytes',
        ]
        return '\n'.join(result)
    
    @command('KEYCOUNT')
    def _handle_keycount(self, args: List[str]) -> str:
        """
        Return the count of keys matching a pattern.
        
        Args:
            args: [pattern] where pattern supports * wildcard
            
        Returns:
            str: Number of matching keys
        """
        pattern = args[0] if args else '*'
        keys = self.store.keys()
        
        if pattern == '*':
            return str(len(keys))
        
        # Simple pattern matching
        import fnmatch
        matched = [k for k in keys if fnmatch.fnmatch(k, pattern)]
        return str(len(matched))
```

Then register the new mixin in `src/command_handler.py`:

```python
from .commands import (
    StringCommands,
    ListCommands,
    CacheCommands,
    StoreCommands,
    UtilityCommands,
    AnalyticsCommands,  # NEW
)

class CommandHandler(
    CommandMixin,
    StringCommands,
    ListCommands,
    CacheCommands,
    StoreCommands,
    UtilityCommands,
    AnalyticsCommands,  # NEW
):
    # ... rest of class
```

And export from `src/commands/__init__.py`:

```python
from .analytics_commands import AnalyticsCommands

__all__ = [
    'StringCommands',
    'ListCommands',
    'CacheCommands',
    'StoreCommands',
    'UtilityCommands',
    'AnalyticsCommands',  # NEW
]
```

## Working with the Command Decorator

The `@command(...)` decorator from `src/commands/base.py` does the following:

1. **Registers command names** - Associates one or more names with the method
2. **Enables auto-discovery** - Adds `_commands` attribute so `CommandHandler` finds it
3. **Supports aliases** - One method can handle multiple command names

### Single Command

```python
@command('MYCOMMAND')
def _handle_mycommand(self, args):
    return 'OK'
```

### Multiple Names (Aliases)

```python
@command('DEL', 'LPOP', 'REMOVE')
def _handle_delete(self, args):
    # Handles DEL, LPOP, and REMOVE
    return 'OK'
```

## Accessing Store Data

Inside command handlers, use `self.store` to access data:

```python
class MyCommands:
    @command('MYCOMMAND')
    def _handle_mycommand(self, args):
        # Store a value
        self.store.set('key', 'value')
        
        # Get a value
        value = self.store.get('key')
        
        # Check if key exists
        if 'key' in self.store:
            del self.store['key']
        
        # Get all keys
        keys = self.store.keys()
        
        # Work with caches
        cache = self.store.get('cache_name')
        
        return 'OK'
```

See `src/expiring_store.py` for full API.

## Accessing Validation

Use `self.validation_handler` to access validation utilities:

```python
class MyCommands:
    @command('MYCOMMAND')
    def _handle_mycommand(self, args):
        # Validate the command
        is_valid, error = self.validation_handler.validate_command(['MYCOMMAND'] + args)
        if not is_valid:
            return f'ERROR: {error}'
        
        return 'OK'
```

## Accessing Other Handlers

Inside command handlers, you can access other handlers:

```python
class MyCommands:
    @command('MYCOMMAND')
    def _handle_mycommand(self, args):
        # Event handler for responses
        self.event_handler.handle_response('OK', send_response)
        
        # Validation handler
        is_valid, msg = self.validation_handler.validate_command(...)
        
        return 'OK'
```

## Best Practices

### 1. Consistent Error Handling

Always return error messages in a consistent format:

```python
@command('MYCOMMAND')
def _handle_mycommand(self, args):
    try:
        key = args[0]
    except IndexError:
        return 'ERROR: Missing argument'
    
    if not key:
        return 'ERROR: Key cannot be empty'
    
    return 'OK'
```

### 2. Documentstring Format

Use this format for all handlers:

```python
@command('MYCOMMAND')
def _handle_mycommand(self, args: List[str]) -> str:
    """
    Handle MYCOMMAND command.
    
    Args:
        args: [arg1, arg2] description of arguments
        
    Returns:
        str: Description of return value
    """
    # implementation
```

### 3. Return Types

- **Success**: Return a string result (e.g., `'OK'`, `'value'`)
- **Not found**: Return `'NULL'`
- **Error**: Return `'ERROR: message'`
- **Multi-line**: Join with `'\n'`

### 4. Type Hints

Always use type hints for arguments and return:

```python
from typing import List

@command('MYCOMMAND')
def _handle_mycommand(self, args: List[str]) -> str:
    """..."""
```

### 5. Thread Safety

The `store`, `event_handler`, and `validation_handler` are thread-safe. You don't need to add locks in your command handlers.

### 6. Testing

Always write unit tests for new commands:

```python
def test_mycommand():
    store = ExpiringStore()
    handler = CommandHandler(store)
    responses = []
    
    handler.handle_command(['MYCOMMAND', 'arg1'], lambda r: responses.append(r))
    assert 'OK' in responses[-1].decode()
```

## Advanced: Custom Command Behavior

### Modifying Command History

Commands are automatically added to history (unless they're HISTORY or REPLAY). To control this:

```python
@command('MYCOMMAND')
def _handle_mycommand(self, args):
    # Your implementation
    return 'OK'
    
# To exclude from history, modify handle_command in CommandHandler
# See: if command != 'HISTORY' and command != 'REPLAY'
```

### Responding with Special Format

For complex responses, return formatted strings:

```python
@command('MYCOMMAND')
def _handle_mycommand(self, args):
    result = ['Line 1', 'Line 2', 'Line 3']
    return '\n'.join(result)
```

### Working with Lists and Caches

```python
@command('MYLISTCOMMAND')
def _handle_mylistcommand(self, args):
    key = args[0]
    current = self.store.get(key, [])
    
    if not isinstance(current, list):
        current = [current] if current != 'NULL' else []
    
    current.append(args[1])
    self.store.set(key, current)
    
    return 'OK'
```

## Troubleshooting

### Command Not Found

If your command returns "Unknown command":

1. Check decorator: `@command('MYCOMMAND')`
2. Verify method is public: `def _handle_mycommand`
3. Check inheritance: Is your mixin inherited in `CommandHandler`?
4. Restart server: Changes require restart

### Validation Errors

If your command fails validation:

1. Add specs to `validation_handler.py`: `_command_specs`
2. Check argument count matches min/max
3. Verify argument types if needed

### Server Doesn't Start

If adding a command breaks the server:

1. Check syntax errors: `python -m py_compile src/commands/my_commands.py`
2. Check imports: Are all modules imported?
3. Check inheritance: Did you add mixin to `CommandHandler`?
4. Check for circular imports

## Testing Your Changes

```bash
# Check syntax
python -m py_compile src/commands/my_commands.py

# Run unit tests
python -m unittest discover -s tests/unit

# Run integration tests (requires running server)
python -m unittest discover -s tests/integration

# Manual test
python server.py
# In another terminal:
telnet localhost 6379
```

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for deep dive into design
- Read [USER_GUIDE.md](USER_GUIDE.md) for command reference
- Check existing command modules for code style
- Join discussions about new features
