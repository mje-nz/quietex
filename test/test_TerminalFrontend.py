"""Tests for TerminalFrontend."""
# pylint: disable=protected-access,invalid-name

import re
from typing import Callable, List

import pyte

from quietex.frontend import TerminalFrontend
from test.test_BasicFrontend import (
    EXAMPLE_OUTPUT,
    EXAMPLE_QUIET,
    EXAMPLE_VERBOSE,
    _frontend_integration_test,
)


class AtScreen(pyte.Screen):
    """Pyte screen with the background filled with @s for better testing."""

    @property
    def default_char(self):
        """The background character."""
        return pyte.screens.Char("@")

    def reset(self):
        """Reset the terminal to its initial state."""
        super().reset()
        # Cursor has to have the same character as the background or erasing won't work
        self.cursor.attrs = self.default_char


class FakeTerminalFrontend(TerminalFrontend):
    """TerminalFrontend which outputs to a Pyte emulated terminal instead of stdout."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.screen = AtScreen(80, 24)
        self.stream = pyte.Stream(self.screen)
        self.pre_input_hooks: List[Callable] = []

    def _input(self, raw_prompt):
        self._write(raw_prompt)
        for hook in self.pre_input_hooks:
            hook()
        # Simulate input
        self.stream.feed("\r\n")
        return ""

    def _write(self, raw_value):
        # Swap \n for \r\n
        raw_value = re.sub(r"([^\r])\n", r"\1\r\n", raw_value)
        if raw_value == "\n":
            raw_value = "\r\n"
        # Write to terminal
        self.stream.feed(raw_value)
        return len(raw_value)

    def _get_terminal_width(self):
        return self.screen.columns

    def assert_cursor(self, x, y):  # pylint: disable=invalid-name
        """Assert the cursor is at (`x`, `y`)."""
        assert (self.screen.cursor.x, self.screen.cursor.y) == (x, y)

    def assert_display_like(self, lines, message=None):
        """Make an assertion about what's on the display.

        If `lines` is a string, assert the first line of the display is equal to it.  If
        `lines` is a list of strings, assert each line of the display is equal to the
        corresponding line from the list.  Line endings will be checked.
        """
        if isinstance(lines, str):
            lines = [lines]
        for i, line in enumerate(lines):
            actual = self.screen.display[i]
            expected = (line + self.screen.default_char.data)[: self.screen.columns]

            # Format display line for assertion failure message
            try:
                actual_end_index = actual.index(self.screen.default_char.data)
            except ValueError:
                actual_end_index = self.screen.columns
            actual_to_print = actual[: max(len(expected), actual_end_index)]
            error = f"Failed at line {i}, {repr(actual_to_print)} should be {expected}"
            if message is not None:
                error = f"{message}: {error}"
            assert actual.startswith(expected), error


def test_faketerminalfrontend_write_line():
    r"""Test FakeTerminalFrontend.write handles a line terminated by \n properly."""
    frontend = FakeTerminalFrontend()
    frontend._write("test\n")
    frontend.assert_cursor(0, 1)


def test_faketerminalfrontend_write_blank_line():
    """Test FakeTerminalFrontend.write handles a line followed by a blank line properly."""
    frontend = FakeTerminalFrontend()
    frontend._write("test\n\n")
    frontend.assert_cursor(0, 2)


def test_faketerminalfrontend_write_newline():
    r"""Test FakeTerminalFrontend.write handles a \n on its own properly."""
    frontend = FakeTerminalFrontend()
    frontend._write("test")
    frontend._write("\n")
    frontend.assert_cursor(0, 1)


def test_faketerminalfrontend_write_newlines():
    r"""Test FakeTerminalFrontend.write handles multiple \ns on their own properly."""
    frontend = FakeTerminalFrontend()
    frontend._write("test")
    frontend._write("\n\n")
    frontend.assert_cursor(0, 2)


def test_faketerminalfrontend_wrap_line():
    r"""Test FakeTerminalFrontend.write wraps at 80 characters."""
    frontend = FakeTerminalFrontend()
    frontend._write("x" * 100)
    frontend.assert_display_like(["x" * 80, "x" * 20])


def test_print():
    """Test basic use of print."""
    frontend = FakeTerminalFrontend()
    frontend.print("test")
    frontend.assert_display_like(["test", ""])
    frontend.assert_cursor(0, 1)


def test_print_multiple_lines():
    """Test printing multiple lines (without status)."""
    frontend = FakeTerminalFrontend()
    frontend.print("test1")
    frontend.print("test2")
    frontend.assert_display_like(["test1", "test2", ""])


def test_print_with_status():
    """Test basic use of print with a status line."""
    frontend = FakeTerminalFrontend()
    frontend.print("test1")
    frontend.print("test2 [1]")
    frontend.assert_display_like(["test1", "test2 [1]", "[1]", ""])


def test_print_multiple_lines_with_status():
    """Test the status line stays at the bottom when multiple lines are printed."""
    frontend = FakeTerminalFrontend()
    frontend.print("test1 [1]")
    frontend.print("test2")
    frontend.assert_display_like(["test1 [1]", "[1]", "test2", "[1]", ""])

    frontend.print("test3")
    frontend.assert_display_like(["test1 [1]", "[1]", "test2", "test3", "[1]", ""])


def test_input():
    """Test faking input when no status line has been printed."""
    frontend = FakeTerminalFrontend()
    frontend.print("test")
    frontend.pre_input_hooks = [
        lambda: frontend.assert_display_like(["test", "? ", ""]),
        lambda: frontend.assert_cursor(2, 1),
    ]
    frontend.input("? ")
    frontend.assert_display_like(["test", "? ", ""])

    frontend.print("test2")
    frontend.assert_display_like(["test", "? ", "test2", ""])


def test_input_after_status():
    """Test input prompt prints without status line."""
    frontend = FakeTerminalFrontend()
    frontend.print("test1 [1]")
    frontend.print("test2")
    frontend.pre_input_hooks = [
        lambda: frontend.assert_display_like(["test1 [1]", "[1]", "test2", "? ", ""]),
        lambda: frontend.assert_cursor(2, 3),
    ]
    frontend.input("? ")
    frontend.assert_display_like(["test1 [1]", "[1]", "test2", "? ", ""])

    frontend.print("test3")
    frontend.assert_display_like(
        ["test1 [1]", "[1]", "test2", "? ", "test3", "[1]", ""]
    )


def test_log_clears_status():
    """Test that printing a log message either clears or leaves status correctly."""
    frontend = FakeTerminalFrontend()
    frontend.print("test [1]")
    frontend.log("log")
    frontend.assert_display_like(["test [1]", "[1]", "log", "[1]", ""])
    frontend.log("log2")
    frontend.assert_display_like(["test [1]", "[1]", "log", "log2", "[1]", ""])


def test_verbose():
    """Test printing each type of token in verbose mode."""
    _frontend_integration_test(FakeTerminalFrontend(), EXAMPLE_OUTPUT, EXAMPLE_VERBOSE)


def test_quiet():
    """Test printing each type of token in quiet mode."""
    frontend = FakeTerminalFrontend(quiet=True)
    _frontend_integration_test(frontend, EXAMPLE_OUTPUT, EXAMPLE_QUIET)


def test_line_wrap():
    """Test clearing status bars that are so long they wrap around."""
    frontend = FakeTerminalFrontend()
    msg = (
        "(/a/very/long/filename/which/is/so/long/that/it/wraps/around/onto/the/next"
        "/line/of/the/terminal"
    )
    frontend.print(msg)
    frontend.assert_display_like([msg[:80], msg[80:], msg[:80], msg[80:] + ")"])
    frontend.print("test")
    frontend.print("test2")
    frontend.assert_display_like(
        [
            # Original message
            msg[:80],
            msg[80:],
            # Status bar, since it changed
            msg[:80],
            msg[80:] + ")",
            # Plain text
            "test",
            "test2",
            # Status bar
            msg[:80],
            msg[80:] + ")",
        ]
    )


def test_print_partial_simple():
    """Test printing partial lines with a simple example."""
    frontend = FakeTerminalFrontend()
    frontend.print("Partial", finished=False)
    frontend.assert_display_like("Partial", "")

    frontend.print("Full")
    frontend.assert_display_like("Full", "")


def test_print_partial_complex():
    """Test printing partial lines with a long example including status changes."""
    frontend = FakeTerminalFrontend()
    msg = "(./test.tex [1] (./test2.tex test message [2]))"
    for i in range(1, 4):
        # No valid file yet
        frontend.print(msg[:i], finished=False)
        frontend.assert_display_like([msg[:i], ""], i)
    for i in range(4, 12):
        # Part-way through test.tex
        frontend.print(msg[:i], finished=False)
        frontend.assert_display_like([msg[:i], msg[:i] + ")", ""], i)
    for i in range(12, 14):
        # Part-way through start page
        frontend.print(msg[:i], finished=False)
        frontend.assert_display_like([msg[:i], "(./test.tex)", ""], i)
    for i in range(21, 29):
        # Partway through second file
        frontend.print(msg[:i], finished=False)
        frontend.assert_display_like([msg[:i], msg[12:i] + ")", ""], i)
    for i in range(29, 44):
        # Not up to second page yet
        frontend.print(msg[:i], finished=False)
        frontend.assert_display_like([msg[:i], "[1] (./test2.tex)", ""], i)
    for i in range(44, 45):
        # Not up to close files yet
        frontend.print(msg[:i], finished=False)
        frontend.assert_display_like([msg[:i], "[2] (./test2.tex)", ""], i)
    # Close second file
    frontend.print(msg[:-1], finished=False)
    frontend.assert_display_like([msg[:-1], "[2] (./test.tex)", ""])
    # Close first file
    frontend.print(msg)
    frontend.assert_display_like([msg, "[2]", ""])
