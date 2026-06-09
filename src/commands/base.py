"""
Base classes and utilities for command handlers.

This module provides the command decorator and base handler utilities
used by all command modules.
"""

from typing import List


def command(*names: str):
    """
    Decorator that registers a handler method for one or more command names.

    Usage::

        @command('SET')
        def handle_set(self, args): ...

        @command('DEL', 'LPOP')   # alias multiple names to one handler
        def handle_del(self, args): ...

    The decorated method gains a ``_commands`` attribute (list of upper-cased
    names) which ``CommandHandler.__init__`` discovers automatically via
    ``inspect``.  No manual dispatch table is needed.
    """
    def decorator(func):
        func._commands = [n.upper() for n in names]
        return func
    return decorator


class CommandMixin:
    """Base mixin for command handler classes."""

    def _get_history(self) -> List[str]:
        """
        Get the command history, respecting max_history_size.

        Returns:
            List[str]: List of commands in history
        """
        if self.max_history_size == 0:
            return list(self.command_history)
        return self.command_history[-self.max_history_size:]
