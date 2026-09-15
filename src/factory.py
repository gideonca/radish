"""
Service factory for initializing and managing Radish services.

This module centralizes creation of the server's long-lived singletons so that
startup, dependency wiring, and teardown are all defined in one place.

Usage:
    ServiceFactory.initialize()
    store = ServiceFactory.get_store()
    command_handler = ServiceFactory.get_command_handler()
"""

from typing import Any, Dict, Optional, Type

from .command_handler import CommandHandler
from .event_handler import EventHandler
from .expiring_store import ExpiringStore
from .logging_handler import LoggingHandler
from .persistence_handler import PersistenceHandler


class ServiceFactory:
    """Factory for creating and managing service singletons."""

    _services: Dict[str, Any] = {}

    @classmethod
    def initialize(
        cls,
        auto_backup_interval: int = 0,
    ) -> "ServiceFactory":
        """
        Initialize all services and return the factory class for chaining.

        Args:
            auto_backup_interval (int): Interval in seconds for auto-backup.
                Defaults to 0 (disabled). Set to a positive value to enable.
        """
        store = ExpiringStore()
        persistence = PersistenceHandler(
            auto_backup_interval=auto_backup_interval,
            store=store,
        )
        command_handler = CommandHandler(store)
        event_handler = EventHandler()
        logging_handler = LoggingHandler()

        cls._services = {
            "store": store,
            "persistence": persistence,
            "command_handler": command_handler,
            "event_handler": event_handler,
            "logging_handler": logging_handler,
        }
        return cls

    @classmethod
    def _get_service(cls, name: str, expected_type: Optional[Type] = None) -> Any:
        """Fetch a service from the registry or raise a clear runtime error."""
        service = cls._services.get(name)
        if service is None:
            raise RuntimeError(
                "ServiceFactory not initialized. Call ServiceFactory.initialize() first."
            )
        if expected_type is not None and not isinstance(service, expected_type):
            raise TypeError(f"Service '{name}' is not of type {expected_type.__name__}")
        return service

    @classmethod
    def get_store(cls) -> ExpiringStore:
        """Get the ExpiringStore singleton."""
        return cls._get_service("store", ExpiringStore)

    @classmethod
    def get_persistence(cls) -> PersistenceHandler:
        """Get the PersistenceHandler singleton."""
        return cls._get_service("persistence", PersistenceHandler)

    @classmethod
    def get_command_handler(cls) -> CommandHandler:
        """Get the CommandHandler singleton."""
        return cls._get_service("command_handler", CommandHandler)

    @classmethod
    def get_event_handler(cls) -> EventHandler:
        """Get the EventHandler singleton."""
        return cls._get_service("event_handler", EventHandler)

    @classmethod
    def get_logging_handler(cls) -> LoggingHandler:
        """Get the LoggingHandler singleton."""
        return cls._get_service("logging_handler", LoggingHandler)

    @classmethod
    def reset(cls) -> None:
        """Reset all singletons and stop background threads."""
        store = cls._services.get("store")
        persistence = cls._services.get("persistence")

        if store is not None:
            store.stop()
        if persistence is not None:
            persistence.stop()

        cls._services = {}
