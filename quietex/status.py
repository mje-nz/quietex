"""Manage application state and status bar."""

from typing import List, Optional

import attr
from attr import attrs

from .lexer import IO, State


@attrs(auto_attribs=True, frozen=True)
class AppState:
    """Manage application state and status bar."""

    current_page: Optional[int] = None
    file_stack: List[str] = attr.Factory(list)

    @property
    def current_file(self):
        """The file currently being processed."""
        if self.file_stack:
            return self.file_stack[-1]
        return None

    def update(self, token_source):
        """Update current file and page based on tokens to print."""
        next_page = self.current_page
        next_stack = self.file_stack.copy()
        for token_type, value in token_source:
            if token_type == State.StartPage:
                next_page = int(value.strip("[] "))
            elif token_type == IO.OpenFile:
                next_stack.append(value.strip("("))
            elif token_type == IO.CloseFile:
                try:
                    next_stack.pop()
                except IndexError:
                    pass
        return AppState(next_page, next_stack)

    def format_status(self):
        """Return the current status bar as a string, and reset dirtiness."""
        status = ""
        if self.current_page:
            status += f"[{self.current_page}]"
        if self.current_file:
            status += f" ({self.current_file})"
            status = status.strip(" ")
        return status
