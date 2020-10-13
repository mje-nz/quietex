"""Tests for BasicFrontend."""
# pylint: disable=invalid-name

import io

from quietex.frontend import BasicFrontend


class StringBasicFrontend(BasicFrontend):
    """BasicIO which records its outputs in a StringIO."""

    def __init__(self):
        super().__init__()
        self._output = io.StringIO()

    def _write(self, raw_value):
        return self._output.write(raw_value)

    @property
    def output(self):
        """Everything printed so far, as a string."""
        return self._output.getvalue()


def test_simple():
    """Print some output and check that the status bar is updated correctly."""
    frontend = StringBasicFrontend()
    frontend.print("Test")
    assert frontend.output == "Test\n"


def test_state():
    """Check that printing StartPage and OpenFile triggers the status bar."""
    frontend = StringBasicFrontend()
    frontend.print("(./test.tex [1]")
    assert frontend.output == "(./test.tex [1]\n[1] (./test.tex)\n"


# TODO: quiet mode
