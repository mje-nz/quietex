"""Tests for command-line interface."""
import re
import subprocess


def remove_control_sequences(line: str):
    """Remove ANSI controls sequences from a string."""
    # https://stackoverflow.com/a/33925425
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


def test_cli_works():
    """Test that the CLI is in the path, and passes through output."""
    cmd = ["quietex", "--quiet", "echo", "test"]
    output = subprocess.run(cmd, text=True, check=True, capture_output=True).stdout
    assert remove_control_sequences(output).strip() == "test"


def test_latexmkrc():
    """Test that quietex --latexmkrc prints something vaguely correct."""
    cmd = ["quietex", "--latexmkrc"]
    output = subprocess.run(cmd, text=True, check=True, capture_output=True).stdout
    assert re.search(r'\$pdflatex = ".*?quietex \$pdflatex"', output)
