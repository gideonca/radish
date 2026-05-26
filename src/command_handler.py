"""
Command handler for the Reddish server.

This module implements a Redis-like command handler using the command pattern.
It processes incoming commands and manages interactions with the data store.
"""
import inspect
from typing import List, Callable, Dict
from .expiring_store import ExpiringStore
from .validation_handler import ValidationHandler
from .event_handler import EventHandler


def command(*names: str):
    """
    Decorator that registers a handler method for one or more command names.

    Usage::

        @command('SET')
        def _handle_set(self, args): ...

        @command('DEL', 'LPOP')   # alias multiple names to one handler
        def _handle_del(self, args): ...

    The decorated method gains a ``_commands`` attribute (list of upper-cased
    names) which ``CommandHandler.__init__`` discovers automatically via
    ``inspect``.  No manual dispatch table is needed.
    """
    def decorator(func):
        func._commands = [n.upper() for n in names]
        return func
    return decorator

class CommandHandler:
    """
    Handles execution of Redis-like commands using a command dispatcher pattern.
    
    This class provides a clean interface for executing Redis-style commands
    against a data store. It uses a dispatcher pattern for efficient command 
    routing and consistent error handling.
    
    Attributes:
        store (ExpiringStore): The backing store for data persistence
        _handlers (Dict): Mapping of commands to their handler methods
        event_handler (EventHandler): Handler for event-related functionality
        validation_handler (ValidationHandler): Handler for command validation
    """

    def __init__(self, store: ExpiringStore):
        """
        Initialize a new CommandHandler instance.

        Args:
            store (ExpiringStore): The data store to use for operations
        """
        self.event_handler = EventHandler()
        self.validation_handler = ValidationHandler()
        self.store = store
        self.command_history = []  # Stores last n commands where n = max_history_size 
        self.max_history_size = 0 # Increase size, if size == 0 there is no limit

        # Auto-discover handlers: any method decorated with @command(...) is
        # registered here.  No manual mapping needed — just add a new method.
        self._handlers: Dict[str, Callable] = {}
        for _, method in inspect.getmembers(self, predicate=inspect.ismethod):
            for cmd in getattr(method, '_commands', []):
                self._handlers[cmd] = method

    def _preprocess_set_command(self, command_parts: List[str]) -> List[str]:
        """
        Preprocess SET command to handle JSON values with spaces.
        
        Args:
            command_parts: Original command parts
            
        Returns:
            List[str]: Processed command parts with JSON value combined
        """
        if len(command_parts) < 3:
            return command_parts
            
        # If this is a SET command with more parts than expected,
        # combine all parts after the key into a single value
        if command_parts[0].upper() == 'SET' and len(command_parts) > 3:
            return [
                command_parts[0],
                command_parts[1],
                ' '.join(command_parts[2:])
            ]
        return command_parts

    def handle_command(self, command_parts: List[str], send_response: Callable) -> bool:
        """
        Handle a command and send response through the callback.
        
        Args:
            command_parts: List of command parts (command and arguments)
            send_response: Callback function to send response to client
            
        Returns:
            bool: True if connection should stay open, False to close
        """
        if not command_parts:
            return True

        # TODO: Need to implement command logging here

        # Preprocess command parts to handle JSON values with spaces
        command_parts = self._preprocess_set_command(command_parts)
        command = command_parts[0].upper()
        
        if command == 'EXIT':
            return self.event_handler.handle_exit(send_response)
            
        is_valid, error_msg = self.validation_handler.validate_command(command_parts)
        if not is_valid:
            self.event_handler.handle_error(error_msg, send_response)
            return True

        try:
            handler = self._handlers.get(command)
            if not handler:
                raise ValueError(f'Unknown command: {command}')
            
            # Record command in history
            if command != 'HISTORY' and command != 'REPLAY': # Avoid logging HISTORY and REPLAY commands
                command_history_entry = ' '.join(command_parts)
                self.command_history.append(command_history_entry)
            
            # Remove oldest if exceeding max size
            if self.max_history_size > 0: # No limit if == 0
                if len(self.command_history) > self.max_history_size:
                    self.command_history.pop(0)
                
            response = handler(command_parts[1:])
            self.event_handler.handle_response(response, send_response)
        except Exception as e:
            self.event_handler.handle_error(str(e), send_response)
            
        return True

    @command('PING')
    def _handle_ping(self, args: List[str]) -> str:
        """Handle PING command."""
        return r"""
                     .-.
                    (o o)  
                    | O \
                    \   \
                    `~~~'
                    /     \
                   /       \
                  /         \
                 /           \
                /             \
               /               \
               -----------------
                    I LIVE
                """

    @command('ECHO')
    def _handle_echo(self, args: List[str]) -> str:
        """
        Handle ECHO command.
        
        Args:
            args: List of arguments to echo back
            
        Returns:
            str: The joined arguments as a single string
        """
        return ' '.join(args)

    @command('SET')
    def _handle_set(self, args: List[str]) -> str:
        """
        Handle SET command.
        
        Args:
            args: [key, value] to store
            
        Returns:
            str: 'OK' on success
        """
        key, value = args[0], args[1]
        self.store.set(key, value)
        return 'OK'

    @command('GET')
    def _handle_get(self, args: List[str]) -> str:
        """
        Handle GET command.
        
        Args:
            args: [key] to retrieve
            
        Returns:
            str: The value or 'NULL' if not found
        """
        key = args[0]
        return str(self.store.get(key, 'NULL'))

    @command('DEL', 'LPOP')
    def _handle_del(self, args: List[str]) -> str:
        """
        Handle DEL/LPOP command.
        
        Args:
            args: [key] to delete
            
        Returns:
            str: 'OK' if deleted, 'NULL' if key didn't exist
        """
        key = args[0]
        if key in self.store:
            del self.store[key]
            return 'OK'
        return 'NULL'

    @command('EXPIRE')
    def _handle_expire(self, args: List[str]) -> str:
        """
        Handle EXPIRE command.
        
        Args:
            args: [key, ttl] where ttl is in seconds
            
        Returns:
            str: 'OK' if expiry set, 'NULL' if key didn't exist
        """
        key, ttl = args[0], int(args[1])
        if key in self.store:
            value = self.store.get(key)
            self.store.set(key, value, ttl=ttl)
            return 'OK'
        return 'NULL'

    @command('LPUSH')
    def _handle_lpush(self, args: List[str]) -> str:
        """
        Handle LPUSH command.
        
        Args:
            args: [key, value] to prepend
            
        Returns:
            str: 'OK' on success
        """
        key, value = args[0], args[1]
        current = self.store.get(key, [])
        print(current)
        if not isinstance(current, list):
            current = [current] if current != 'NULL' else []
        current.insert(0, value)  # Insert at the beginning of the list
        self.store.set(key, current)
        return 'OK'

    @command('RPUSH')
    def _handle_rpush(self, args: List[str]) -> str:
        """
        Handle RPUSH command.
        
        Args:
            args: [key, value] to append
            
        Returns:
            str: 'OK' on success
        """
        key, value = args[0], args[1]
        current = self.store.get(key, [])
        if not isinstance(current, list):
            current = [current] if current != 'NULL' else []
        current.append(value)
        self.store.set(key, current)
        return 'OK'

    @command('INSPECT')
    def _handle_inspect(self, args: List[str]) -> str:
        """
        Handle INSPECT command.
        
        Returns:
            str: Formatted string of all key-value pairs
        """
        result = []
        for k in self.store.keys():
            v = self.store.get(k)
            result.append(f'{k}: {v}')
        result.append('END')
        return '\n'.join(result)

    @command('CREATECACHE')
    def _handle_create_cache(self, args: List[str]) -> str:
        """
        Handle CREATECACHE command.
        
        Args:
            args: [cache_name] name of the cache to create
            
        Returns:
            str: 'OK' if cache was created, error message if it already exists
        """
        cache_name = args[0]
        if self.store.create_cache(cache_name):
            return 'OK'
        return f'Cache {cache_name} already exists'

    @command('DELETECACHE')
    def _handle_delete_cache(self, args: List[str]) -> str:
        """
        Handle DELETECACHE command.
        
        Args:
            args: [cache_name] name of the cache to delete
            
        Returns:
            str: 'OK' if cache was deleted, error message if it didn't exist
        """
        cache_name = args[0]
        if self.store.delete_cache(cache_name):
            return 'OK'
        return f'Cache {cache_name} does not exist'

    @command('LISTCACHES')
    def _handle_list_caches(self, args: List[str]) -> str:
        """
        Handle LISTCACHES command.
        
        Returns:
            str: Formatted string listing all cache names
        """
        caches = self.store.list_caches()
        if not caches:
            return 'No caches exist'
        result = ['Available caches:']
        for cache in caches:
            size = self.store.get_cache_size(cache)
            result.append(f'- {cache} ({size} items)')
        return '\n'.join(result)

    @command('CACHESET')
    def _handle_cache_set(self, args: List[str]) -> str:
        """
        Handle CACHESET command.
        
        Args:
            args: [cache_name, key, value]
            
        Returns:
            str: 'OK' if successful, error message otherwise
        """
        cache_name, key, value = args[0], args[1], args[2]
        
        # Auto-create cache if it doesn't exist
        if cache_name not in [c for c in self.store.list_caches()]:
            self.store.create_cache(cache_name)
        
        if self.store.cache_set(cache_name, key, value):
            return 'OK'
        return f'Failed to set {key} in cache {cache_name}'

    @command('CACHEGET')
    def _handle_cache_get(self, args: List[str]) -> str:
        """
        Handle CACHEGET command.
        
        Args:
            args: [cache_name, key]
            
        Returns:
            str: The value or 'NULL' if not found
        """
        cache_name, key = args[0], args[1]
        value = self.store.cache_get(cache_name, key, 'NULL')
        return str(value)

    @command('CACHEDEL')
    def _handle_cache_del(self, args: List[str]) -> str:
        """
        Handle CACHEDEL command.
        
        Args:
            args: [cache_name, key]
            
        Returns:
            str: 'OK' if deleted, error message otherwise
        """
        cache_name, key = args[0], args[1]
        if self.store.cache_delete(cache_name, key):
            return 'OK'
        return f'Key {key} not found in cache {cache_name}'

    @command('CACHEKEYS')
    def _handle_cache_keys(self, args: List[str]) -> str:
        """
        Handle CACHEKEYS command.
        
        Args:
            args: [cache_name]
            
        Returns:
            str: Formatted list of all keys in the cache
        """
        cache_name = args[0]
        keys = self.store.cache_keys(cache_name)
        if not keys:
            return f'No keys in cache {cache_name}'
        return '\n'.join(keys)

    @command('CACHEGETALL')
    def _handle_cache_get_all(self, args: List[str]) -> str:
        """
        Handle CACHEGETALL command.        

        
        Args:handle_command
            args: [cache_name]
            
        Returns:
            str: JSON representation of all key-value pairs in the cache
        """
        import json
        cache_name = args[0]
        cache_data = self.store.cache_get_all(cache_name)
        
        if cache_data is None:
            return f'Cache {cache_name} does not exist'
        
        if not cache_data:
            return '{}'
        
        return json.dumps(cache_data, indent=2)


    @command('CREATESTORE')
    def _handle_create_store(self, args: List[str]) -> str:
        """
        Handle CREATESTORE command.
        
        Args:
            args: [cache_name, store_name, ttl?] where ttl is optional in seconds
            
        Returns:
            str: 'OK' if store was created, error message otherwise
        """
        cache_name, store_name = args[0], args[1]
        ttl = float(args[2]) if len(args) > 2 else None
        
        try:
            store = ExpiringStore(default_ttl=ttl)
            if self.store.set(cache_name, {store_name: store}):
                return 'OK'
            return f'Failed to create store {store_name} in cache {cache_name}'
        except Exception as e:
            return f'Error creating store: {str(e)}'

    @command('DELETESTORE')
    def _handle_delete_store(self, args: List[str]) -> str:
        """
        Handle DELETESTORE command.
        
        Args:
            args: [cache_name, store_name]
            
        Returns:
            str: 'OK' if store was deleted, error message if it didn't exist
        """
        cache_name, store_name = args[0], args[1]
        cache = self.store.get(cache_name)
        
        if not cache:
            return f'Cache {cache_name} does not exist'
            
        if store_name not in cache:
            return f'Store {store_name} does not exist in cache {cache_name}'
            
        store = cache[store_name]
        if isinstance(store, ExpiringStore):
            store.stop()  # Stop the cleanup thread
            
        del cache[store_name]
        return 'OK'

    @command('LISTSTORES')
    def _handle_list_stores(self, args: List[str]) -> str:
        """
        Handle LISTSTORES command.
        
        Args:
            args: [cache_name]
            
        Returns:
            str: Formatted string listing all stores in the cache
        """
        cache_name = args[0]
        cache = self.store.get(cache_name)
        
        if not cache:
            return f'Cache {cache_name} does not exist'
            
        stores = [name for name, value in cache.items() 
                 if isinstance(value, ExpiringStore)]
        
        if not stores:
            return f'No stores in cache {cache_name}'
            
        result = [f'Stores in cache {cache_name}:']
        for store_name in stores:
            store = cache[store_name]
            num_items = len(store.keys())
            ttl = store.default_ttl or 'No'
            result.append(f'- {store_name} ({num_items} items, {ttl} TTL)')
        return '\n'.join(result)
    
    @command('HISTORY')
    def _handle_history(self, args: List[str]) -> str:
        """
        Handle HISTORY command.
        
        Returns:
            str: Formatted string of the last 20 commands executed
        """
        if self.max_history_size == 0:
            history = list(self.command_history)
        else:
            history = self.command_history[-self.max_history_size:]

        if not history:
            return 'No commands in history'

        result = ['Command History:']
        for i, cmd in enumerate(history, 1):
            result.append(f'{i}: {cmd}')
        return '\n'.join(result)
    
    @command('REPLAY')
    def _handle_replay(self, args: List[str]) -> str:
        """
        Handle REPLAY command.
        
        Returns:
            str: 'OK' if replayed successfully, error message otherwise
        """
        import shlex

        if self.max_history_size == 0:
            history = list(self.command_history)
        else:
            history = self.command_history[-self.max_history_size:]

        if not history:
            return 'No commands in history'

        try:
            index = int(args[0])
        except (TypeError, ValueError):
            return 'Invalid history index'

        if index < 1 or index > len(history):
            return 'History index out of range'

        cmd = history[index - 1]
        command_parts = shlex.split(cmd)
        if not command_parts:
            return 'Invalid command in history'

        command_parts = self._preprocess_set_command(command_parts)
        command = command_parts[0].upper()
        handler = self._handlers.get(command)
        if not handler:
            return f'Unknown command: {command}'

        return handler(command_parts[1:])