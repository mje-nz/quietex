"""Tests for TerminalFrontend."""
# pylint: disable=protected-access,invalid-name

import re
from typing import Callable, List

import pyte

from quietex.frontend import TerminalFrontend


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

    def __init__(self):
        super().__init__()
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

    def assert_cursor(self, x, y):  # pylint: disable=invalid-name
        """Assert the cursor is at (`x`, `y`)."""
        assert (self.screen.cursor.x, self.screen.cursor.y) == (x, y)

    def assert_display_like(self, lines):
        """Make an assertion about what's on the display.

        If `lines` is a string, assert the first line of the display is equal to it.  If
        `lines` is a list of strings, assert each line of the display is equal to the
        corresponding line from the list.  Line endings will be checked.
        """
        if isinstance(lines, str):
            lines = [lines]
        for i, line in enumerate(lines):
            expected = line + self.screen.default_char.data
            actual = self.screen.display[i]
            assert actual.startswith(
                expected
            ), f"{repr(actual)} should start with {expected}"


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


# TODO: quiet mode
# TODO: case where line wraps and \r doesn't work correctly
