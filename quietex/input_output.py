"""Input and output handling.

Author: Matthew Edwards
Date: August 2019
"""
import sys
from typing import Optional

from colorama import Style


class BasicIo:  # pylint: disable=too-many-instance-attributes
    """Handle input and output."""

    def __init__(self, auto_status=True, use_style=True):
        """Set up IO state.

        Args:
            auto_status (bool): Print status line automatically when the page number or
                currently-open file changes.
            use_style (bool): If False, ignore all style arguments.
        """
        self.auto_status = auto_status
        self.use_style = use_style
        self.page: Optional[str] = None
        self.file: Optional[str] = None
        self.status_style = None
        self._last_page: Optional[str] = None
        self._last_file: Optional[str] = None

    def _input(self, raw_prompt):
        """Display a prompt and return the user's input."""
        return input(raw_prompt)

    def input(self, prompt, style=None):
        """Display a prompt with the given style and return the user's input."""
        if style and self.use_style:
            prompt = style + prompt + Style.RESET_ALL
        return self._input(prompt)

    def _write(self, raw_value):
        """Write directly to the underlying output.

        Returns:
            int: number of characters written.
        """
        return sys.stdout.write(raw_value)

    def _print(self, value: str, end="\n", style: str = None):
        """Print `value` then `end` with the given character style.

        Returns:
            int: number of characters written.
        """
        length = 0
        if style and self.use_style:
            length += self._write(style)
        length += self._write(value + end)
        if style and self.use_style:
            length += self._write(Style.RESET_ALL)
        return length

    def print_status(self, end="\n"):
        """Print the status line followed by `end`.

        Returns:
            int: number of characters written.
        """
        status = ""
        if self.page:
            status += f"[{self.page}]"
        if self.file:
            status += f" ({self.file})"
            status = status.strip(" ")
        length = self._print(status, end=end, style=self.status_style)
        self._last_page = self.page
        self._last_file = self.file
        return length

    def _flush(self):
        return sys.stdout.flush()

    def print(self, value="", end="\n", style: str = None):
        """Print a value, then print the status line if it has changed."""
        length = self._print(value, end, style)
        status_changed = self.page != self._last_page or self.file != self._last_file
        if end == "\n" and status_changed and self.auto_status:
            length += self.print_status()
        self._flush()
        return length


class TerminalIo(BasicIo):
    """Handle input from and output to a terminal."""

    CURSOR_TO_START = "\x1b[G"
    DELETE_WHOLE_LINE = "\x1b[2K"

    def __init__(self):
        super().__init__()
        self.keep_last_status = False

    def _clear_status(self):
        """If the last thing printed was the status line, clear it."""
        if self.keep_last_status:
            # Finish status line first
            self._write("\n")
            self.keep_last_status = False
        else:
            # Clear status line first
            self._write(self.CURSOR_TO_START + self.DELETE_WHOLE_LINE)

    def input(self, *args, **kwargs):  # pylint: disable=arguments-differ
        """Display a prompt with the given style and return the user's input.

        The status line will be cleared if it is displayed, and it will not be
        re-printed until after the next line of output.
        """
        self._clear_status()
        return super().input(*args, **kwargs)

    def print(self, value="", end="\n", style: str = None):
        """Print a value then update the status line, maintaining it at the bottom.

        The status line is still printed an extra time if it has changed.
        """
        self._clear_status()
        self._print(value, end, style)
        if end == "\n" and self.page != self._last_page or self.file != self._last_file:
            self.keep_last_status = True
        self.print_status(end="")
        self._flush()
