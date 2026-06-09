"""Cache management commands (CREATECACHE, CACHESET, CACHEGET, etc.)."""

from typing import List
from .base import command


class CacheCommands:
    """Cache management command handlers."""

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

        Args:
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
