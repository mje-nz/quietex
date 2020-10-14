"""Handle formatting tokens."""
# pylint: disable=redefined-builtin

import blessings
from pygments import format
from pygments.formatter import Formatter

from .lexer import *  # noqa: F403

__all__ = ["AnsiTerminalFormatter", "contains_error", "format", "quiet_filter"]


def contains_error(token_source):
    """Return whether a list of tokens contains an error token."""
    for token_type, _ in token_source:
        if token_type == Generic.Error:
            return True
    return False


def quiet_filter(token_source):
    """Filter a list of tokens to remove IO message for quiet mode."""
    return [
        (token_type, value)
        for (token_type, value) in token_source
        if IO not in (token_type, token_type.parent)
    ]


class AnsiTerminalFormatter(Formatter):
    """Handle formatting tokens with ANSI styles."""

    def __init__(self, terminal=None):
        super().__init__()
        if terminal is None:
            terminal = blessings.Terminal()

        self.style = {
            IO.CloseFile: terminal.dim,
            IO.OpenFile: terminal.dim,
            IO.ReadAux: terminal.dim,
            IO.ReadImage: terminal.dim,
            Generic.Error: terminal.bright_red,
            Generic.Warning: terminal.yellow,
            UI.Prompt: terminal.red,
            UI.Status: terminal.blue,
            UI.Message: terminal.dim,
        }

    def format_unencoded(self, token_source, outfile):
        """Format a list of tokens.

        Called internally by Formatter.format.
        """
        for token_type, value in token_source:
            assert "\n" not in value
            if token_type in self.style:
                value = self.style[token_type](value)
            outfile.write(value)
