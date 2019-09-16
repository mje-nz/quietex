"""Formatting logic for QuieTeX output."""

from collections import defaultdict
from typing import List

import blessings

from .tokens import *  # noqa: F403


def hide(value):
    """Don't print this string (use like a blessings format)."""
    return ""


class LatexLogFormatter(object):
    """Formatter for QuieTeX output."""

    def __init__(self, terminal=blessings.Terminal(), quiet=True):  # noqa: B008
        self.stack = []
        self.page = None
        if quiet:
            self.style = {
                CloseFileToken: hide,
                ErrorToken: terminal.bright_red,
                OpenFileToken: hide,
                ReadAuxToken: hide,
                ReadImageToken: hide,
                WarningToken: terminal.yellow,
            }
        else:
            self.style = {
                CloseFileToken: terminal.dim,
                ErrorToken: terminal.bright_red,
                OpenFileToken: terminal.dim,
                ReadAuxToken: terminal.dim,
                ReadImageToken: terminal.dim,
                WarningToken: terminal.yellow,
            }
        self.style = defaultdict(lambda: (lambda val: val), self.style)

    @property
    def file(self):
        """The file currently being processed."""
        if len(self.stack) > 0:
            return self.stack[-1]

    def _format_tokens(self, tokens: List[Token]):
        """Convert a tokens into a string of their values and formatting codes."""
        result = ""
        for token in tokens:
            result += self.style[type(token)](token.text)
        return result

    def process_tokens(self, tokens: List[Token]):
        """Process a list of tokens."""
        for token in tokens:
            if type(token) is PageToken:
                self.page = token.value
            elif type(token) is OpenFileToken:
                self.stack.append(token.value)
            elif type(token) is CloseFileToken:
                try:
                    self.stack.pop()
                except IndexError:
                    pass
        return self._format_tokens(tokens)
