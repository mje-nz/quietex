"""Tests for command-line interface."""
# pylint: disable=redefined-outer-name,unused-argument
import importlib.resources as pkg_resources
import re
import subprocess
from pathlib import Path
from typing import List

import pytest

import quietex
from quietex.cli import main


def remove_control_sequences(line: str):
    """Remove ANSI controls sequences from a string."""
    # https://stackoverflow.com/a/33925425
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


def run(cmd: List[str]) -> str:
    """Run a command in a subprocess, check it succeeds, and return its stdout."""
    return subprocess.run(cmd, text=True, check=True, capture_output=True).stdout


def _run_quietex_internal(args: List[str], capsys) -> str:
    """Call the quietex main function and return its stdout.

    Args:
        args: quietex CLI arguments
        capsys: instance of pytest capsys fixture
    """
    main(args)
    return capsys.readouterr().out


@pytest.fixture(params=["script", "module", "internal"])
def run_quietex(request, capsys):
    """Run quietex, repeating the test for each way of running it."""
    if request.param == "script":
        # Run `quietex` on the command line
        yield lambda args: run(["quietex"] + args)
    elif request.param == "module":
        # Run `python -m quietex` on the command line
        yield lambda args: run(["python", "-m", "quietex"] + args)
    else:
        # Run quietex in-process, so it's debuggable and coverage sees it
        yield lambda args: _run_quietex_internal(["quietex"] + args, capsys)


def test_cli_works(run_quietex):
    """Test that the CLI is in the path, and passes through output."""
    output = run_quietex(["--quiet", "echo", "test"])
    assert remove_control_sequences(output).strip() == "test"


@pytest.mark.parametrize(
    "args", ("", "--force", "--verbose --no-bell", "--force --verbose --no-bell")
)
def test_latexmkrc(run_quietex, args):
    """Test that quietex --latexmkrc prints something vaguely correct."""
    cmd = ["--latexmkrc"]
    if args:
        cmd += args.split(" ")
    output = run_quietex(cmd)
    assert re.search(r'\$pdflatex = ".*?quietex .*?\$pdflatex"', output)
    for arg in args.split(" "):
        if arg != "--force":
            assert arg in output


# pylint: disable=invalid-name
installed_only = pytest.mark.skipif(
    Path(quietex.__file__) == Path(__file__).parent.parent / "src/quietex/__init__.py",
    reason="installed package only",
)


@installed_only
def test_sentinel_file_missing():
    """Test that when quietex is installed, the sentinel file is missing.

    This is to make sure we're definitely running tests against the installed version
    (not against the source or an editable install), since the sentinel file doesn't
    make it into the wheel.
    """
    with pytest.raises(FileNotFoundError):
        pkg_resources.read_text(quietex, "sentinel.txt")


def latexmkrc(args="--latekmkrc"):
    """Generate example latexmkrc file."""
    return f"eval `quietex {args}`;"


def document():
    """Generate example LaTeX document."""
    return r"""
    \documentclass{article}
    \begin{document}
    Test
    \end{document}
    """


def test_latexmk(in_temp_dir):
    """Test running latexmkrc with the QuieTeX integration."""
    open("latexmkrc", "w").write(latexmkrc())
    open("main.tex", "w").write(document())
    output = run(["latexmk"])
    assert Path("main.tex").exists()
    assert output.strip().endswith("are up-to-date")

    # No "QuieTeX enabled" message, and no $pdflatex already defined warning
    assert "quietex" not in output.lower()


@pytest.mark.parametrize(
    "quietex_args,cmd_args",
    (("--quiet", ""), ("--quiet", "--quiet"), ("--quiet", "test -- -n --help")),
)
def test_arguments_are_untouched(quietex_args, cmd_args):
    """Test that quietex passes through exactly the right arguments to the command."""
    echo_args = str(Path(__file__).parent / "echo_args")
    cmd = ["quietex"] + quietex_args.split(" ") + [echo_args] + cmd_args.split(" ")
    output = run([a for a in cmd if a])
    assert remove_control_sequences(output).strip() == cmd_args
