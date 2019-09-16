"""Tests for formatting module."""

import blessings
import pytest

from quietex.formatting import LatexLogFormatter
from quietex.tokens import *  # noqa: F403


@pytest.fixture
def term():
    """Construct a blessings Terminal that always produces formatting codes."""
    return blessings.Terminal(kind="xterm-256color", force_styling=True)


def test_formatting_empty():
    """Test formatting an empty list of tokens."""
    f = LatexLogFormatter()
    assert f.process_tokens([]) == ""


all_tokens = [
    CloseFileToken(),
    ErrorToken("error"),
    NewlineToken(),
    OpenFileToken("(./open.tex ", "./open.tex"),
    OtherToken("other "),
    PageToken("[1]", "1"),
    ReadAuxToken("{./aux.map}"),
    ReadImageToken("<./image.png>"),
    WarningToken("warning"),
]


def test_formatting_quiet(term):
    """Test formatting every kind of token in quiet mode."""
    f = LatexLogFormatter(term, quiet=True)
    result = f.process_tokens(all_tokens)
    expected = term.bright_red("error") + "\nother [1]" + term.yellow("warning")
    assert result == expected


def test_formatting_verbose(term):
    """Test formatting every kind of token in verbose mode."""
    f = LatexLogFormatter(term, quiet=False)
    result = f.process_tokens(all_tokens)
    expected = (
        term.dim(")")
        + term.bright_red("error")
        + "\n"
        + term.dim("(./open.tex ")
        + "other [1]"
        + term.dim("{./aux.map}")
        + term.dim("<./image.png>")
        + term.yellow("warning")
    )
    assert result == expected


def test_process_page_number(term):
    """Test that processing a page token sets the page correctly."""
    f = LatexLogFormatter(term)
    assert f.page is None
    f.process_tokens([PageToken("[1]", "1")])
    assert f.page == "1"


def test_process_page_numbers(term):
    """Test that processing multiple page tokens sets the page correctly."""
    f = LatexLogFormatter(term)
    assert f.page is None
    f.process_tokens(
        [
            PageToken("[1]", "1"),
            OpenFileToken("(./test.tex", "./test.tex"),
            CloseFileToken(),
            PageToken("[2]", "2"),
        ]
    )
    assert f.page == "2"


def test_process_open_files(term):
    """Test that processing an open file sets the file correctly."""
    f = LatexLogFormatter(term)
    assert f.file is None
    f.process_tokens([OpenFileToken("(./test.tex", "./test.tex")])
    assert f.file == "./test.tex"


def test_process_open_close_files(term):
    """Test that processing open and closie files sets the file correctly."""
    f = LatexLogFormatter(term)

    f.process_tokens([OpenFileToken("(./test.tex", "./test.tex")])
    assert f.file == "./test.tex"

    f.process_tokens([OpenFileToken("(./test2.tex", "./test2.tex")])
    assert f.file == "./test2.tex"

    f.process_tokens([CloseFileToken()])
    assert f.file == "./test.tex"

    f.process_tokens([CloseFileToken()])
    assert f.file is None
