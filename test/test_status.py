"""Tests for status module."""

import pytest

from quietex.lexer import IO, Generic, State, Text
from quietex.status import AppState


def test_create_appstate():
    """Check initial values on new AppState."""
    state = AppState()
    assert state.current_page is None
    assert state.current_file is None


# Status bar formatting


def test_format_status_empty():
    """Test formatting status bar with no current page and file."""
    state = AppState()
    assert state.format_status() == ""


def test_format_status_page_only():
    """Test formatting status bar with only a current page."""
    state = AppState(current_page=1)
    assert state.format_status() == "[1]"


def test_format_status_file_only():
    """Test formatting status bar with only a current file."""
    state = AppState(file_stack=["./test.tex"])
    assert state.format_status() == "(./test.tex)"


def test_format_status_page_and_file():
    """Test formatting status bar with a current page and file."""
    state = AppState(current_page=1, file_stack=["./test.tex"])
    assert state.format_status() == "[1] (./test.tex)"


# Updating state from tokens


@pytest.mark.parametrize(
    "token",
    (
        (Generic.Error, "error"),
        (Text, " text "),
        (State.EndPage, "]"),
        (IO.ReadAux, "{./aux.map}"),
        (IO.ReadImage, "<./image.png>"),
        (Generic.Warning, "warning"),
    ),
)
def test_next_state_no_change(token):
    """Test that most tokens don't change the state."""
    state = AppState()
    next_state = state.update([token])
    assert next_state == state


@pytest.mark.parametrize(
    "tokens",
    (
        [(State.StartPage, "[2 ")],
        [(State.StartPage, "[1"), (State.EndPage, "]"), (State.StartPage, "[2 ")],
    ),
)
def test_next_state_page(tokens):
    """Test the current page changes when StartPage tokens are seen."""
    state = AppState()
    next_state = state.update(tokens)
    assert next_state.current_page == 2
    assert next_state != state


@pytest.mark.parametrize(
    "tokens,expected_file",
    (
        ([(IO.OpenFile, "(./test.tex")], "./test.tex"),
        ([(IO.OpenFile, "(./test.tex"), (IO.OpenFile, "(./test2.tex")], "./test2.tex"),
    ),
)
def test_next_state_file(tokens, expected_file):
    """Test the current file changes when OpenFile and CloseFile tokens are seen."""
    state = AppState()
    next_state = state.update(tokens)
    assert next_state.current_file == expected_file
    assert next_state != state


@pytest.mark.parametrize(
    "tokens", ([(IO.OpenFile, "(./test.tex"), (IO.CloseFile, ")")],)
)
def test_next_state_empty_stack(tokens):
    """Test emptying the file stack."""
    state = AppState()
    next_state = state.update(tokens)
    assert next_state.current_file is None
    assert next_state == state
