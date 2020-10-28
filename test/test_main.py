import os
from typing import Optional

import pexpect
import pyte
import pytest

from .test_TerminalFrontend import AtScreen


class Terminal:
    def __init__(self):
        self.screen = AtScreen(80, 24)
        self.stream = pyte.Stream(self.screen)

    def feed(self, data):
        self.stream.feed(data)

    @property
    def output_lines(self):
        # Make sure cursor is at the bottom
        for i in range(self.screen.cursor.y + 1, self.screen.lines):
            for char in self.screen.buffer[i]:
                assert char.data == self.screen.default_char

        # Get the parts of the screen containing output
        lines = [self.screen.buffer[i] for i in range(self.screen.cursor.y + 1)]
        return [
            "".join(
                line[i].data
                for i in range(self.screen.columns)
                if line[i].data != self.screen.default_char.data
            )
            for line in lines
        ]


def test_output_lines_empty():
    term = Terminal()
    assert term.output_lines == [""]


def test_output_lines():
    term = Terminal()
    term.feed("Test\n")
    assert term.output_lines == ["Test", ""]


class QuietexRunner:
    def __init__(self, cmd):
        self.terminal = Terminal()
        env = dict(os.environ, TERM="xterm")
        self.process = pexpect.spawn(
            cmd[0], cmd[1:], encoding="utf-8", timeout=5, env=env
        )

    @property
    def is_alive(self):
        return self.process.isalive()

    def poll(self, timeout=None):
        if timeout is None:
            timeout = -1
        try:
            self.terminal.feed(
                self.process.read_nonblocking(size=100000, timeout=timeout)
            )
        except (pexpect.TIMEOUT, pexpect.EOF):
            pass

    @property
    def output_lines(self):
        self.poll()
        return self.terminal.output_lines


@pytest.fixture
def tmp_fifo(tmp_path):
    fifo_path = tmp_path / "fifo"
    os.mkfifo(fifo_path)
    return fifo_path


def test_simple(tmp_fifo):
    quietex = QuietexRunner(["quietex", "cat", str(tmp_fifo)])
    assert quietex.output_lines == ["QuieTeX enabled", ""]

    with open(tmp_fifo, "w") as fifo:
        fifo.write("Test\r\n")
        fifo.flush()
        assert quietex.output_lines[1:] == ["Test", ""]

    assert not quietex.is_alive
    assert quietex.output_lines[2:] == [""]
