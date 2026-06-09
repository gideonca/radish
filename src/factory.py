"""
Service factory for initializing and managing Radish services.

This module provides a centralized factory pattern to create and manage
singletons for the store, persistence handler, command handler, and logging
handler. It eliminates import-time side effects and makes testing easier.

Usage:
    ServiceFactory.initialize()
    store = ServiceFactory.get_store()
    command_handler = ServiceFactory.get_command_handler()
"""

from typing import Optional
from .expiring_store import ExpiringStore
from .command_handler import CommandHandler
from .persistence_handler import PersistenceHandler
from .event_handler import EventHandler
from .logging_handler import LoggingHandler


class ServiceFactory:
    """Factory for creating and managing service singletons."""

    _store: Optional[ExpiringStore] = None
    _persistence: Optional[PersistenceHandler] = None
    _command_handler: Optional[CommandHandler] = None
    _event_handler: Optional[EventHandler] = None
    _logging_handler: Optional[LoggingHandler] = None

    @classmethod
    def initialize(
        cls,
        auto_backup_interval: int = 300,
    ) -> None:
        """
        Initialize all services.

        Args:
            auto_backup_interval (int): Interval in seconds for auto-backup.
                Defaults to 300 (5 minutes).
        """
        # Create store first (no dependencies)
        cls._store = ExpiringStore()

        # Create persistence handler (depends on store)
        cls._persistence = PersistenceHandler(
            auto_backup_interval=auto_backup_interval,
            store=cls._store,
        )

        # Create command handler (depends on store)
        cls._command_handler = CommandHandler(cls._store)

        # Create handlers
        cls._event_handler = EventHandler()
        cls._logging_handler = LoggingHandler()

    @classmethod
    def get_store(cls) -> ExpiringStore:
        """
        Get the ExpiringStore singleton.

        Returns:
            ExpiringStore: The backing data store

        Raises:
            RuntimeError: If factory has not been initialized
        """
        if cls._store is None:
            raise RuntimeError(
                "ServiceFactory not initialized. Call ServiceFactory.initialize() first."
            )
        return cls._store

    @classmethod
    def get_persistence(cls) -> PersistenceHandler:
        """
        Get the PersistenceHandler singleton.

        Returns:
            PersistenceHandler: The persistence handler

        Raises:
            RuntimeError: If factory has not been initialized
        """
        if cls._persistence is None:
            raise RuntimeError(
                "ServiceFactory not initialized. Call ServiceFactory.initialize() first."
            )
        return cls._persistence

    @classmethod
    def get_command_handler(cls) -> CommandHandler:
        """
        Get the CommandHandler singleton.

        Returns:
            CommandHandler: The command handler

        Raises:
            RuntimeError: If factory has not been initialized
        """
        if cls._command_handler is None:
            raise RuntimeError(
                "ServiceFactory not initialized. Call ServiceFactory.initialize() first."
            )
        return cls._command_handler

    @classmethod
    def get_event_handler(cls) -> EventHandler:
        """
        Get the EventHandler singleton.

        Returns:
            EventHandler: The event handler

        Raises:
            RuntimeError: If factory has not been initialized
        """
        if cls._event_handler is None:
            raise RuntimeError(
                "ServiceFactory not initialized. Call ServiceFactory.initialize() first."
            )
        return cls._event_handler

    @classmethod
    def get_logging_handler(cls) -> LoggingHandler:
        """
        Get the LoggingHandler singleton.

        Returns:
            LoggingHandler: The logging handler

        Raises:
            RuntimeError: If factory has not been initialized
        """
        if cls._logging_handler is None:
            raise RuntimeError(
                "ServiceFactory not initialized. Call ServiceFactory.initialize() first."
            )
        return cls._logging_handler

    @classmethod
    def reset(cls) -> None:
        """
        Reset all singletons. Useful for testing.

        Stops all background threads before resetting.
        """
        if cls._store is not None:
            cls._store.stop()
        if cls._persistence is not None:
            cls._persistence.stop()

        cls._store = None
        cls._persistence = None
        cls._command_handler = None
        cls._event_handler = None
        cls._logging_handler = None
