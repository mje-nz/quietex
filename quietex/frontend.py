"""Input and output handling.

Author: Matthew Edwards
Date: August 2019
"""
import shutil
import sys
from typing import Any, List, Tuple

from pygments.formatters import NullFormatter

# pylint: disable=redefined-builtin
from .formatter import AnsiTerminalFormatter, contains_error, format, quiet_filter
from .lexer import UI, LatexLogLexer, lex
from .status import AppState


class BasicFrontend:
    """Handle input and output with optional colour but no cursor movement."""

    def __init__(self, color=True, quiet=False, bell_on_error=False):
        self.quiet = quiet
        self.bell_on_error = bell_on_error
        self.state = AppState()
        self.lexer = LatexLogLexer()
        if color:
            self.formatter = AnsiTerminalFormatter()
        else:
            self.formatter = NullFormatter()

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
        sys.stdout.write(raw_value)
        sys.stdout.flush()  # Make sure lines without newlines are printed

    def _print_tokens(self, tokens: List[Tuple[Any, str]], end="\n"):
        """Highlight and print a list of tokens, updating app state if necessary."""
        if not tokens:
            # Make sure blank lines get printed
            self._write(end)
            return 0
        if self.quiet:
            tokens = quiet_filter(tokens)
        if self.bell_on_error and contains_error(tokens):
            end += "\a"
        if tokens:
            # Skip line if it's now empty to avoid lone newline
            self._write(format(tokens, self.formatter) + end)
        length = len("".join(value for (_, value) in tokens))
        return length

    def _print_status(self, status, end="\n"):
        self._print_tokens([(UI.Status, status)], end=end)

    def log(self, message):
        """Print a log message."""
        self._print_tokens([(UI.LogMessage, message)])

    def print(self, value: str, finished=True):
        """Lex, highlight, and print a line of LaTeX compiler output.

        Args:
            value: Line of LaTeX compiler output to print.
            finished: Whether the line is complete, i.e., ended in a newline.
        """
        if not finished:
            return
        tokens = lex(value, self.lexer)
        self._print_tokens(tokens)
        new_state = self.state.update(tokens)
        if new_state != self.state:
            self._print_status(new_state.format_status())
            self.state = new_state


class TerminalFrontend(BasicFrontend):
    """Handle input and output with cursor movement and optional colour."""

    CURSOR_UP = "\x1b[A"
    CURSOR_TO_START = "\x1b[G"
    DELETE_WHOLE_LINE = "\x1b[2K"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keep_last_status = False
        self.last_line_length = None

    def _get_terminal_width(self):
        return shutil.get_terminal_size().columns

    def _clear_status(self):
        """Clear the status bar (unless marked keep) and last line (if not finished)."""
        if self.keep_last_status:
            # Finish status line first
            self._write("\n")
            self.keep_last_status = False
        else:
            last_status_length = len(self.state.format_status())
            # Status bar doesn't end in a newlineClear status bar first
            self._write(self.CURSOR_TO_START + self.DELETE_WHOLE_LINE)
            # Clear previous lines if the status bar is more than one line long
            for _ in range(last_status_length // self._get_terminal_width()):
                self._write(self.CURSOR_UP + self.DELETE_WHOLE_LINE)

            # Also clear last line printed if it wasn't finished
            if self.last_line_length:
                for _ in range(self.last_line_length // self._get_terminal_width() + 1):
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
        self._print_status(self.state.format_status(), end="")

    def print(self, value="", finished=True):  # pylint: disable=arguments-differ
        """Lex, highlight, and print a line of LaTeX compiler output."""
        self._clear_status()
        tokens = lex(value, self.lexer)
        length = self._print_tokens(tokens)
        new_state = self.state.update(tokens)
        self._print_status(new_state.format_status(), end="")
        if finished:
            self.last_line_length = None
        else:
            self.last_line_length = length
        if finished and new_state != self.state:
            self.state = new_state
            self.keep_last_status = True
