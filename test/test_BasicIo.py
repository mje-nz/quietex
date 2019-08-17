"""Tests for BasicIo."""

from colorama import Fore, Style

from quietex.input_output import BasicIo


class FakeIo(BasicIo):
    """BasicIO which records its outputs in a list."""

    def __init__(self):
        super().__init__()
        self.outputs = []

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
    o = FakeIo()
    o.print_status()
    o.assert_last_output("")


def test_print_status_page_only():
    """Test printing status with no file only prints the page number."""
    o = FakeIo()
    o.page = 1
    o.print_status()
    o.assert_last_output("[1]")


def test_print_status_file_only():
    """Test printing status with no page number only prints the file."""
    o = FakeIo()
    o.file = "./test.tex"
    o.print_status()
    o.assert_last_output("(./test.tex)")


def test_print_status_page_and_file():
    """Test printing status with page number and file."""
    o = FakeIo()
    o.page = 1
    o.file = "./test.tex"
    o.print_status()
    o.assert_last_output("[1] (./test.tex)")


def test_print_status_colour():
    """Test printing status with page number and file."""
    o = FakeIo()
    o.page = 1
    o.file = "./test.tex"
    o.status_style = Fore.RED
    o.print_status()
    o.assert_last_output(Fore.RED + "[1] (./test.tex)" + Style.RESET_ALL)


def test_status_prints_when_page_changes():
    """Test printing normally causes the status to print when the page changes."""
    o = FakeIo()
    o.print("test 1")
    o.page = 1
    o.print("test 2")
    o.assert_output(0, "test 1")
    o.assert_output(1, "test 2")
    o.assert_output(2, "[1]")


def test_status_prints_when_file_changes():
    """Test printing normally causes the status to print when the file changes."""
    o = FakeIo()
    o.print("test 1")
    o.file = "./test.tex"
    o.print("test 2")
    o.assert_output(0, "test 1")
    o.assert_output(1, "test 2")
    o.assert_output(2, "(./test.tex)")
