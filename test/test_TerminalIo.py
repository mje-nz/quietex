"""Tests for TerminalIo."""
# pylint: disable=invalid-name,protected-access

import re
from typing import Callable, List

import pyte
from colorama import Fore

from quietex.input_output import TerminalIo


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


class FakeTerminalIo(TerminalIo):
    """TerminalIO which outputs to a Pyte emulated terminal instead of stdout."""

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

    def assert_cursor(self, x, y):
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


def test_faketerminalio_write_line():
    r"""Test FakeTerminalIo.write handles a line terminated by \n properly."""
    o = FakeTerminalIo()
    o._write("test\n")
    o.assert_cursor(0, 1)


def test_faketerminalio_write_blank_line():
    """Test FakeTerminalIo.write handles a line followed by a blank line properly."""
    o = FakeTerminalIo()
    o._write("test\n\n")
    o.assert_cursor(0, 2)


def test_faketerminalio_write_newline():
    r"""Test FakeTerminalIo.write handles a \n on its own properly."""
    o = FakeTerminalIo()
    o._write("test")
    o._write("\n")
    o.assert_cursor(0, 1)


def test_faketerminalio_write_newlines():
    r"""Test FakeTerminalIo.write handles multiple \ns on their own properly."""
    o = FakeTerminalIo()
    o._write("test")
    o._write("\n\n")
    o.assert_cursor(0, 2)


def test_print():
    """Test basic use of _print."""
    o = FakeTerminalIo()
    o._print("test")
    o.assert_display_like("test")


def test_print_with_default_end():
    """Test _print ends with a newline by default."""
    o = FakeTerminalIo()
    o._print("test")
    o.assert_cursor(0, 1)


def test_print_with_end():
    """Test _print with non-default end."""
    o = FakeTerminalIo()
    o._print("test", end="2")
    o.assert_display_like("test2")
    o.assert_cursor(5, 0)


def test_print_with_style():
    """Test _print with non-default style."""
    o = FakeTerminalIo()
    o._print("test", style=Fore.RED)
    assert {o.screen.buffer[0][i].fg for i in range(4)} == {"red"}


def test_full_print():
    """Test basic use of print."""
    o = FakeTerminalIo()
    o.print("test")
    o.assert_display_like(["test", ""])
    o.assert_cursor(0, 1)


def test_full_print_multiple_lines():
    """Test printing multiple lines (without status)."""
    o = FakeTerminalIo()
    o.print("test1")
    o.print("test2")
    o.assert_display_like(["test1", "test2", ""])


def test_full_print_with_status():
    """Test basic use of print with a status line."""
    o = FakeTerminalIo()
    o.print("test1")
    o.page = "1"
    o.print("test2")
    o.assert_display_like(["test1", "test2", "[1]", ""])


def test_full_print_multiple_lines_with_status():
    """Test the status line stays at the bottom when multiple lines are printed."""
    o = FakeTerminalIo()
    o.page = "1"
    o.print("test1")
    o.print("test2")
    o.assert_display_like(["test1", "[1]", "test2", "[1]", ""])

    o.print("test3")
    o.assert_display_like(["test1", "[1]", "test2", "test3", "[1]", ""])


def test_input():
    """Test faking input when no status line has been printed."""
    o = FakeTerminalIo()
    o.print("test")
    o.pre_input_hooks = [
        lambda: o.assert_display_like(["test", "? ", ""]),
        lambda: o.assert_cursor(2, 1),
    ]
    o.input("? ")
    o.assert_display_like(["test", "? ", ""])

    o.print("test2")
    o.assert_display_like(["test", "? ", "test2", ""])


def test_input_after_status():
    """Test input prompt prints without status line."""
    o = FakeTerminalIo()
    o.page = "1"
    o.print("test1")
    o.print("test2")
    o.pre_input_hooks = [
        lambda: o.assert_display_like(["test1", "[1]", "test2", "? ", ""]),
        lambda: o.assert_cursor(2, 3),
    ]
    o.input("? ")
    o.assert_display_like(["test1", "[1]", "test2", "? ", ""])

    o.print("test3")
    o.assert_display_like(["test1", "[1]", "test2", "? ", "test3", "[1]", ""])
