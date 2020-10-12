"""Tests for BasicIo."""
# pylint: disable=invalid-name,protected-access

import io
from typing import List, Tuple

from colorama import Fore

from quietex.frontend import BasicFrontend


class FakeFrontend(BasicFrontend):
    """BasicIO which records its outputs in a list."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outputs: List[Tuple] = []

    def _print(self, value, end="\n", style=None):
        self.outputs.append((value, end, style))
        return len(value) + len(end)

    def assert_output(self, i, value, end="\n", style=None):
        """Make an assertion about the `i`th output."""
        assert self.outputs[i] == (value, end, style)

    def assert_last_output(self, *args, **kwargs):
        """Make an assertion about the `last output."""
        return self.assert_output(-1, *args, **kwargs)


def test_print_status_empty():
    """Test printing status with no page number or file does nothing."""
    o = FakeFrontend()
    o.print_status()
    o.assert_last_output("")


def test_print_status_page_only():
    """Test printing status with no file only prints the page number."""
    o = FakeFrontend()
    o.page = "1"
    o.print_status()
    o.assert_last_output("[1]")


def test_print_status_file_only():
    """Test printing status with no page number only prints the file."""
    o = FakeFrontend()
    o.file = "./test.tex"
    o.print_status()
    o.assert_last_output("(./test.tex)")


def test_print_status_page_and_file():
    """Test printing status with page number and file."""
    o = FakeFrontend()
    o.page = "1"
    o.file = "./test.tex"
    o.print_status()
    o.assert_last_output("[1] (./test.tex)")


def test_print_status_colour():
    """Test printing status with page number and file."""
    o = FakeFrontend()
    o.page = "1"
    o.file = "./test.tex"
    o.status_style = Fore.RED
    o.print_status()
    o.assert_last_output("[1] (./test.tex)", style=Fore.RED)


def _test_page_change(o: FakeFrontend, end="\n"):
    o.print("test 1")
    o.page = "1"
    o.print("test 2", end=end)
    o.assert_output(0, "test 1")
    o.assert_output(1, "test 2", end)


def test_status_prints_when_page_changes():
    """Test printing normally causes the status to print when the page changes."""
    o = FakeFrontend()
    _test_page_change(o)
    o.assert_output(2, "[1]")


def test_status_doesnt_print_when_page_changes_without_newline():
    """Test the status doesn't print when the page changes without a line ending."""
    o = FakeFrontend()
    _test_page_change(o, end="")
    assert len(o.outputs) == 2


def test_status_doesnt_print_on_page_change_when_disabled():
    """Test the status doesn't print when the page changes if auto-status disabled."""
    o = FakeFrontend(auto_status=False)
    _test_page_change(o)
    assert len(o.outputs) == 2


def _test_file_change(o: FakeFrontend, end="\n"):
    o.print("test 1")
    o.file = "./test.tex"
    o.print("test 2", end=end)
    o.assert_output(0, "test 1")
    o.assert_output(1, "test 2", end)


def test_status_prints_when_file_changes():
    """Test printing normally causes the status to print when the file changes."""
    o = FakeFrontend()
    _test_file_change(o)
    o.assert_output(2, "(./test.tex)")


def test_status_doesnt_print_when_file_changes_without_newline():
    """Test the status doesn't print when the file changes without a line ending."""
    o = FakeFrontend()
    _test_file_change(o, end="")
    assert len(o.outputs) == 2


def test_status_doesnt_print_on_file_change_when_disabled():
    """Test the status doesn't print when the file changes if auto-status disabled."""
    o = FakeFrontend(auto_status=False)
    _test_file_change(o)
    assert len(o.outputs) == 2


class StringBasicFrontend(BasicFrontend):
    """BasicIO which records its outputs in a StringIO."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output = io.StringIO()

    def _write(self, raw_value):
        return self.output.write(raw_value)

    def assert_printed(self, value):
        """Assert the total output (including newlines) equals `value`."""
        assert self.output.getvalue() == value


def test_print_without_style():
    """Test printing with use_style=False doesn't output colour commands."""
    o = StringBasicFrontend(use_style=False)
    o.print("test", style=Fore.RED)
    o.assert_printed("test\n")


def test_input_without_style():
    """Test inputting with use_style=False doesn't output colour commands."""
    o = StringBasicFrontend(use_style=False)
    o._input = lambda prompt: o._print(prompt) and ""  # type: ignore
    o.input("test", style=Fore.RED)
    o.assert_printed("test\n")


def test_print_status_without_style():
    """Test printing status line with use_style=False doesn't output colour commands."""
    o = StringBasicFrontend(use_style=False)
    o.status_style = Fore.BLUE
    o.page = "1"
    o.file = "./test.tex"
    o.print_status()
    o.assert_printed("[1] (./test.tex)\n")
