"""Tests for BasicFrontend."""
# pylint: disable=invalid-name

import io
from typing import List

from quietex.frontend import BasicFrontend


class StringBasicFrontend(BasicFrontend):
    """BasicIO which records its outputs in a StringIO."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._output = io.StringIO()

    def _write(self, raw_value):
        return self._output.write(raw_value)

    def _input(self, raw_prompt):
        self._write(raw_prompt + "\n")
        return ""

    @property
    def output(self):
        """Everything printed so far, as a string."""
        return self._output.getvalue()

    def assert_display_like(self, lines):
        r"""Make an assertion about what's on the display.

        If `lines` is a string, assert that the output so far is equal to it.  If
        `lines` is a list of strings, assert that the output so far is equal to those
        strings joined with \n.

        Roughly compatible with test_TerminalFrontend.FakeTerminalFrontend.
        """
        if isinstance(lines, str):
            lines = [lines]
        assert self.output == "\n".join(lines)


def test_simple():
    """Print some plain text and check that the status bar is not printed."""
    frontend = StringBasicFrontend()
    frontend.print("Test")
    assert frontend.output == "Test\n"


def test_state():
    """Check that printing StartPage and OpenFile triggers the status bar."""
    frontend = StringBasicFrontend()
    frontend.print("(./test.tex [1]")
    assert frontend.output == "(./test.tex [1]\n[1] (./test.tex)\n"


def test_log_newline():
    """Test that printing a log message puts newlines in the right places."""
    frontend = StringBasicFrontend()
    frontend.print("test [1]")
    frontend.log("log")
    assert frontend.output == "test [1]\n[1]\nlog\n"
    frontend.log("log2")
    assert frontend.output == "test [1]\n[1]\nlog\nlog2\n"


EXAMPLE_OUTPUT = [
    "(./open.tex ",
    "error [1]",
    "test",
    "",
    "{./aux.map}",
    "<./image.png>",
    "warning [2]",
    ")",
]
EXAMPLE_VERBOSE = [
    "(./open.tex ",
    "(./open.tex)",
    "error [1]",
    "[1] (./open.tex)",
    "test",
    "",
    "{./aux.map}",
    "<./image.png>",
    "warning [2]",
    "[2] (./open.tex)",
    ")",
    "[2]",
]
EXAMPLE_QUIET = [
    " ",
    "(./open.tex)",
    "error [1]",
    "[1] (./open.tex)",
    "test",
    "",
    "warning [2]",
    "[2] (./open.tex)",
    "[2]",
]


def _frontend_integration_test(frontend, output: List[str], expected: List[str]):
    for line in output:
        frontend.print(line)
    frontend.log("Log message")
    frontend.input("? ")
    frontend.assert_display_like(expected + ["Log message", "? ", ""])


def test_verbose():
    """Test printing each type of token in verbose mode."""
    _frontend_integration_test(StringBasicFrontend(), EXAMPLE_OUTPUT, EXAMPLE_VERBOSE)


def test_quiet():
    """Test printing each type of token in quiet mode."""
    frontend = StringBasicFrontend(quiet=True)
    _frontend_integration_test(frontend, EXAMPLE_OUTPUT, EXAMPLE_QUIET)


def test_error_bell():
    """Test that printing an error adds a bell character."""
    frontend = StringBasicFrontend(bell_on_error=True)
    frontend.print("! Generic error")
    assert "\a" in frontend.output


def test_print_partial():
    """Test that trying to print a partial line does nothing."""
    frontend = StringBasicFrontend()
    frontend.print("test", finished=False)
    assert frontend.output == ""
