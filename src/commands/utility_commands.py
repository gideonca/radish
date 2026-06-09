"""Utility and diagnostic commands (PING, ECHO, INSPECT, HISTORY, REPLAY)."""

import shlex
from typing import List
from .base import command


class UtilityCommands:
    """Utility and diagnostic command handlers."""

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

    @command('HISTORY')
    def _handle_history(self, args: List[str]) -> str:
        """
        Handle HISTORY command.

        Returns:
            str: Formatted string of the last 20 commands executed
        """
        history = self._get_history()
        if not history:
            return 'No commands in history'

        result = ['Command History:']
        for i, cmd in enumerate(history, 1):
            result.append(f'{i}: {cmd}')
        return '\n'.join(result)

    @command('REPLAY')
    def _handle_replay(self, args: List[str]) -> str:
        """
        Handle REPLAY command by index from history.

        Args:
            args: [index] - 1-based index into command history

        Returns:
            str: Result of replayed command or error message
        """
        history = self._get_history()
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
