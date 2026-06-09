"""String key-value commands (SET, GET, DEL, EXPIRE)."""

from typing import List
from .base import command


class StringCommands:
    """String operation command handlers."""

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
