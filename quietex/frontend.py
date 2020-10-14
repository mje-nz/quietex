"""Input and output handling.

Author: Matthew Edwards
Date: August 2019
"""
import shutil
import sys
from typing import Any, List, Tuple

# pylint: disable=redefined-builtin
from .formatter import AnsiTerminalFormatter, format, quiet_filter
from .lexer import UI, LatexLogLexer, lex
from .status import AppState


class BasicFrontend:
    """Handle input and output with optional colour but no cursor movement."""

    def __init__(self, quiet=False):  # pylint: disable=unused-argument
        self.quiet = quiet
        self.state = AppState()
        self.lexer = LatexLogLexer()
        self.formatter = AnsiTerminalFormatter()
        self.last_status_length = 0

    def _input(self, raw_prompt):
        """Display a prompt and return the user's input."""
        return input(raw_prompt)

    def input(self, prompt):
        """Display a prompt (with highlighting) and return the user's input."""
        return self._input(format([(UI.Prompt, prompt)], self.formatter))

    def _write(self, raw_value):
        """Write directly to the underlying output.

        Returns:
            int: number of characters written.
        """
        return sys.stdout.write(raw_value)

    def _print_tokens(self, tokens: List[Tuple[Any, str]], end="\n"):
        """Highlight and print a list of tokens, updating app state if necessary."""
        self.state.update(tokens)
        if self.quiet:
            tokens = list(quiet_filter(tokens))
        if tokens:
            # Skip line if it's now empty
            self._write(format(tokens, self.formatter) + end)

    def print_status(self, end="\n"):
        """Print status bar and reset status bar dirtiness."""
        status = self.state.format_status()
        self.last_status_length = len(status)
        self._print_tokens([(UI.Status, status)], end=end)

    def _flush(self):
        """Flush output to screen."""
        return sys.stdout.flush()

    def log(self, message):
        """Print a log message."""
        self._print_tokens([(UI.LogMessage, message)])

    def print(self, value: str):
        """Lex, highlight, and print a line of LaTeX compiler output."""
        self._print_tokens(lex(value, self.lexer))
        if self.state.status_dirty():
            self.print_status()
        self._flush()


class TerminalFrontend(BasicFrontend):
    """Handle input and output with cursor movement and optional colour."""

    CURSOR_UP = "\x1b[A"
    CURSOR_TO_START = "\x1b[G"
    DELETE_WHOLE_LINE = "\x1b[2K"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keep_last_status = False

    def _get_terminal_width(self):
        return shutil.get_terminal_size().columns

    def _clear_status(self):
        """If the last thing printed was the status line, clear it."""
        if self.keep_last_status:
            # Finish status line first
            self._write("\n")
            self.keep_last_status = False
        else:
            # Clear status bar first
            self._write(self.CURSOR_TO_START + self.DELETE_WHOLE_LINE)
            # Clear previous lines if the status bar is more than one line long
            for _ in range(self.last_status_length // self._get_terminal_width()):
                self._write(self.CURSOR_UP + self.DELETE_WHOLE_LINE)

    def input(self, *args, **kwargs):  # pylint: disable=arguments-differ
        """Display a prompt with the given style and return the user's input.

        The status line will be cleared if it is displayed, and it will not be
        re-printed until after the next line of output.
        """
        self._clear_status()
        return super().input(*args, **kwargs)

    def log(self, message):
        """Print a log message."""
        self._clear_status()
        super().log(message)
        self.print_status(end="")
        self._flush()

    def print(self, value="", end="\n"):  # pylint: disable=arguments-differ
        """Lex, highlight, and print a line of LaTeX compiler output."""
        self._clear_status()
        self._print_tokens(lex(value, self.lexer))
        if end == "\n" and self.state.status_dirty():
            self.keep_last_status = True
        self.print_status(end="")
        self._flush()
