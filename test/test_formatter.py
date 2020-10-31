"""Tests for formatter module."""
# pylint: disable=redefined-outer-name,redefined-builtin

import blessings
import pytest

from quietex.formatter import AnsiTerminalFormatter, format, quiet_filter
from quietex.lexer import *  # noqa: F403


@pytest.fixture
def term():
    """Construct a blessings Terminal that always produces formatting codes."""
    return blessings.Terminal(kind="xterm-256color", force_styling=True)


def test_formatting_empty():
    """Test formatting an empty list of tokens."""
    formatter = AnsiTerminalFormatter()
    assert format([], formatter) == ""


EXAMPLE_TOKENS = [
    (IO.CloseFile, ")"),
    (Generic.Error, "error"),
    (IO.OpenFile, "(./open.tex"),
    (Text, " text "),
    (State.StartPage, "[1"),
    (State.EndPage, "]"),
    (IO.ReadAux, "{./aux.map}"),
    (IO.ReadImage, "<./image.png>"),
    (Generic.Warning, "warning"),
    # TODO: UI
]


def test_formatting_quiet(term):
    """Test formatting every kind of token in quiet mode."""
    formatter = AnsiTerminalFormatter(term)
    result = format(quiet_filter(EXAMPLE_TOKENS), formatter)
    expected = term.bright_red("error") + " text [1]" + term.yellow("warning")
    assert result == expected


def test_log_quiet(term):
    """Make sure log messages are filtered in quiet mode."""
    formatter = AnsiTerminalFormatter(term)
    result = format(quiet_filter([(UI.Message, "log"), (Text, "text")]), formatter)
    assert result == "text"


def test_formatting_verbose(term):
    """Test formatting every kind of token in verbose mode."""
    formatter = AnsiTerminalFormatter(term)
    result = format(EXAMPLE_TOKENS, formatter)
    expected = (
        term.dim(")")
        + term.bright_red("error")
        + term.dim("(./open.tex")
        + " text [1]"
        + term.dim("{./aux.map}")
        + term.dim("<./image.png>")
        + term.yellow("warning")
    )
    assert result == expected
