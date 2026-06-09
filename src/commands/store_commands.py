"""Store management commands (CREATESTORE, DELETESTORE, LISTSTORES)."""

from typing import List
from .base import command


class StoreCommands:
    """Store management command handlers."""

    @command('CREATESTORE')
    def _handle_create_store(self, args: List[str]) -> str:
        """
        Handle CREATESTORE command.

        Args:
            args: [cache_name, store_name, ttl?] where ttl is optional in seconds

        Returns:
            str: 'OK' if store was created, error message otherwise
        """
        from ..expiring_store import ExpiringStore

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
        from ..expiring_store import ExpiringStore

        cache_name, store_name = args[0], args[1]
        cache = self.store.get(cache_name)

        if not cache:
            return f'Cache {cache_name} does not exist'

        if store_name not in cache:
            return f'Store {store_name} does not exist in cache {cache_name}'

        store = cache[store_name]
        if isinstance(store, ExpiringStore):
            store.stop()

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
        from ..expiring_store import ExpiringStore

        cache_name = args[0]
        cache = self.store.get(cache_name)

        if not cache:
            return f'Cache {cache_name} does not exist'

        stores = [
            name for name, value in cache.items()
            if isinstance(value, ExpiringStore)
        ]

        if not stores:
            return f'No stores in cache {cache_name}'

        result = [f'Stores in cache {cache_name}:']
        for store_name in stores:
            store = cache[store_name]
            num_items = len(store.keys())
            ttl = store.default_ttl or 'No'
            result.append(f'- {store_name} ({num_items} items, {ttl} TTL)')
        return '\n'.join(result)
