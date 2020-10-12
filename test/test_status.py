"""Tests for status module."""

from quietex.lexer import IO, State
from quietex.status import AppState

# Basic functionality


def test_status_empty():
    """Test formatting status bar with no current page and file."""
    app = AppState()
    assert app.format_status() == ""


def test_status_page_only():
    """Test formatting status bar with only a current page."""
    app = AppState()
    app.current_page = 1
    assert app.format_status() == "[1]"


def test_status_file_only():
    """Test formatting status bar with only a current file."""
    app = AppState()
    app.current_file = "./test.tex"
    assert app.format_status() == "(./test.tex)"


def test_status_page_and_file():
    """Test formatting status bar with a current page and file."""
    app = AppState()
    app.current_page = 1
    app.current_file = "./test.tex"
    assert app.format_status() == "[1] (./test.tex)"


def test_status_dirty_on_page_change():
    """Test changing page makes the status dirty."""
    app = AppState()
    assert not app.status_dirty()
    app.current_page = 1
    assert app.status_dirty()
    app.format_status()
    assert not app.status_dirty()

    app.current_page = 2
    assert app.status_dirty()
    app.format_status()
    assert not app.status_dirty()


def test_status_dirty_on_file_change():
    """Test changing file makes the status dirty."""
    app = AppState()
    assert not app.status_dirty()
    app.current_file = "./test.tex"
    assert app.status_dirty()
    app.format_status()
    assert not app.status_dirty()

    app.current_file = "./test2.tex"
    assert app.status_dirty()
    app.format_status()
    assert not app.status_dirty()


# Updating state from tokens


def test_process_page():
    """Test the current page changes when a StartPage token is seen."""
    app = AppState()
    assert app.current_page is None
    app.update([(State.StartPage, "[2 ")])
    assert app.current_page == 2


def test_process_multiple_pages():
    """Test the current page changes when several StartPage tokens are seen."""
    app = AppState()
    app.update(
        [(State.StartPage, "[1"), (State.EndPage, "]"), (State.StartPage, "[2 ")]
    )
    assert app.current_page == 2


def test_process_file():
    """Test the current file changes when an OpenFile token is seen."""
    app = AppState()
    assert app.current_file is None
    app.update([(IO.OpenFile, "(./test.tex")])
    assert app.current_file == "./test.tex"


def test_process_open_close_files():
    """Test the current file changes when a CloseFile token is seen."""
    app = AppState()

    app.update([(IO.OpenFile, "(./test.tex"), (IO.OpenFile, "(./test2.tex")])
    assert app.current_file == "./test2.tex"

    app.update([(IO.CloseFile, ")")])
    assert app.current_file == "./test.tex"

    app.update([(IO.CloseFile, ")")])
    assert app.current_file is None
