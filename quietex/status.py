"""Manage application state and status bar."""

from typing import List, Optional

from .lexer import IO, State


class AppState:
    """Manage application state and status bar."""

    def __init__(self):
        self.current_page: Optional[int] = None
        self.file_stack: List[str] = []
        self._last_page_printed: Optional[str] = None
        self._last_file_printed: Optional[int] = None

    @property
    def current_file(self):
        """The file currently being processed."""
        if self.file_stack:
            return self.file_stack[-1]
        return None

    @current_file.setter
    def current_file(self, file):
        """Add a file to the stack."""
        self.file_stack.append(file)

    def update(self, token_source):
        """Update current file and page based on tokens to print."""
        for token_type, value in token_source:
            if token_type == State.StartPage:
                self.current_page = int(value.strip("[] "))
            elif token_type == IO.OpenFile:
                self.current_file = value.strip("(")
            elif token_type == IO.CloseFile:
                try:
                    self.file_stack.pop()
                except IndexError:
                    pass

    def status_dirty(self):
        """Return whether the status bar has changed since it was last printed."""
        return (
            self.current_page != self._last_page_printed
            or self.current_file != self._last_file_printed
        )

    def format_status(self):
        """Return the current status bar as a string, and reset dirtiness."""
        status = ""
        if self.current_page:
            status += f"[{self.current_page}]"
        if self.current_file:
            status += f" ({self.current_file})"
            status = status.strip(" ")
        self._last_page_printed = self.current_page
        self._last_file_printed = self.current_file
        return status
