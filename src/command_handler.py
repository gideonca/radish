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
from .commands.base import CommandMixin
from .commands import (
    StringCommands,
    ListCommands,
    CacheCommands,
    StoreCommands,
    UtilityCommands,
)


class CommandHandler(
    CommandMixin,
    StringCommands,
    ListCommands,
    CacheCommands,
    StoreCommands,
    UtilityCommands,
):
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
