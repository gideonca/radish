"""List operation commands (LPUSH, RPUSH)."""

from typing import List
from .base import command


class ListCommands:
    """List operation command handlers."""

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
        if not isinstance(current, list):
            current = [current] if current != 'NULL' else []
        current.insert(0, value)
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
