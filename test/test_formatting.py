"""Tests for formatting module."""

import io
from unittest.mock import Mock

import pytest
from colorama import Fore, Style

from quietex.formatting import LatexLogFormatter
from quietex.input_output import BasicIo
from quietex.parsing import *  # noqa: F403


def test_print_other():
    """Test printing an uninteresting message."""
    tty = Mock(BasicIo)
    f = LatexLogFormatter()
    f.handle_tokens(tty, [OtherToken("test")])
    tty.print.assert_any_call("test", end="", style=None)
    # TODO: Check actual output, not call


def test_print_multiple():
    """Test printing multiple messages."""
    tty = Mock(BasicIo)
    f = LatexLogFormatter()
    f.handle_tokens(tty, [OtherToken("test"), OtherToken("test2")])
    tty.print.assert_any_call("test", end="", style=None)
    tty.print.assert_any_call("test2", end="", style=None)


def test_print_error():
    """Test printing an error message."""
    tty = Mock(BasicIo)
    f = LatexLogFormatter()
    f.handle_tokens(tty, [ErrorToken("test")])
    tty.print.assert_any_call("test", end="", style=Style.BRIGHT + Fore.RED)


def test_print_warning():
    """Test printing a warning message."""
    tty = Mock(BasicIo)
    f = LatexLogFormatter()
    f.handle_tokens(tty, [WarningToken("test")])
    tty.print.assert_any_call("test", end="", style=Fore.YELLOW)


def test_print_open_close_page():
    """Test (not) printing open/close/page messages."""
    tty = Mock(BasicIo)
    f = LatexLogFormatter()
    f.handle_tokens(
        tty,
        [
            OpenFileToken("(./test.tex", "./test.tex"),
            CloseFileToken(),
            PageToken("[1]", "1"),
        ],
    )
    # Just enough for status line
    tty.print.assert_called_with()


def test_handle_page_numbers():
    """Test that handling multiple page tokens sets the page on the io correctly."""
    tty = Mock(BasicIo)
    f = LatexLogFormatter()
    f.handle_tokens(
        tty,
        [
            PageToken("[1]", "1"),
            OpenFileToken("(./test.tex", "./test.tex"),
            CloseFileToken(),
            PageToken("[2]", "2"),
        ],
    )
    assert tty.page == "2"


def test_handling_page_number_updates_status():
    """Test that handling a page number token causes the status line to be printed."""
    tty = Mock(BasicIo)
    f = LatexLogFormatter()
    f.handle_tokens(tty, [PageToken("[1]", "1")])
    tty.print.assert_called()


def test_handle_open_files():
    """Test that opening files sets the file on the io."""
    tty = Mock(BasicIo)
    f = LatexLogFormatter()
    f.handle_tokens(tty, [OpenFileToken("(./test.tex", "./test.tex")])
    assert tty.file == "./test.tex"


def test_handle_open_close_files():
    """Test that opening and closing files sets the file on the io correctly."""
    tty = Mock(BasicIo)
    f = LatexLogFormatter()

    f.handle_tokens(tty, [OpenFileToken("(./test.tex", "./test.tex")])
    assert tty.file == "./test.tex"

    f.handle_tokens(tty, [OpenFileToken("(./test2.tex", "./test2.tex")])
    assert tty.file == "./test2.tex"

    f.handle_tokens(tty, [CloseFileToken()])
    assert tty.file == "./test.tex"

    f.handle_tokens(tty, [CloseFileToken()])
    assert tty.file is None


# TODO: Dedupe
class StringBasicIo(BasicIo):
    """BasicIO which records its outputs in a StringIO."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output = io.StringIO()

    def _write(self, raw_value):
        return self.output.write(raw_value)


def test_print_open_non_quiet():
    """Test printing an open message with quiet=False."""
    tty = StringBasicIo(auto_status=False, use_style=False)
    f = LatexLogFormatter(quiet=False)
    f.handle_tokens(tty, [OpenFileToken("(./test.tex", "./test.tex")])
    assert tty.output.getvalue() == "(./test.tex\n"


@pytest.mark.skip
def test_print_open_close_non_quiet():
    """Test printing an open.close message with quiet=False."""
    tty = StringBasicIo(auto_status=False, use_style=False)
    f = LatexLogFormatter(quiet=False)
    f.handle_tokens(tty, [OpenFileToken("(./test.tex", "./test.tex"), CloseFileToken()])
    assert tty.output.getvalue() == "(./test.tex)\n"
