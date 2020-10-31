"""Main program implementation."""
import importlib.resources as pkg_resources
import os
import sys
import textwrap
from typing import List

import pexpect

from ._meta import __version__  # noqa: F401
from .frontend import BasicFrontend, TerminalFrontend  # noqa: F401


def handle_prompt(tty: BasicFrontend, pdflatex: pexpect.spawn):
    """Check if pdflatex has prompted for user input and if so handle it.

    If the "? " prompt is detected, prompt the user for a command (or Ctrl+C or
    Ctrl+D) and pass their response to pdflatex.
    """
    if pdflatex.buffer != "? ":
        # It's not waiting for input
        return
    try:
        prompt = pdflatex.read(2)
    except pexpect.exceptions.TIMEOUT:
        # It's not waiting for input
        return
    while True:
        # pdflatex needs a newline after Ctrl+C, so loop until we get a proper
        # response from the user
        try:
            user_response = tty.input(prompt)
            pdflatex.send(user_response + "\n")
            return
        except EOFError:
            # Ctrl+D at input prompt (pdflatex responds immediately)
            pdflatex.sendcontrol("d")
            return
        except KeyboardInterrupt:
            # Ctrl+C at input prompt (pdflatex responds at end of line)
            pdflatex.sendintr()
            prompt = ""


def run_command(cmd: List[str], **kwargs):
    """Run the command, filtering and colouring its output.

    The command is assumed to be a pdflatex invocation, but other LaTeX compilers
    probably work too.

    Args:
        cmd: Command to run, and its arguments.
        quiet: Whether to completely hide useless output or just dim it.
    """
    # Disable pdflatex line wrap (where possible)
    env = dict(os.environ, max_print_line="1000000000")

    # Run pdflatex and filter/colour output
    pdflatex = pexpect.spawn(cmd[0], cmd[1:], env=env, encoding="utf-8", timeout=0.2)

    tty = TerminalFrontend(**kwargs)
    # tty = BasicFrontend(quiet=quiet)
    tty.log("QuieTeX enabled")

    while True:
        try:
            line = pdflatex.readline()
        except pexpect.exceptions.TIMEOUT:
            # Check if it's waiting for input
            handle_prompt(tty, pdflatex)
            continue
        if line == "":
            # EOF
            break

        # TODO: Page numbers would work better if it parsed the line bit by bit
        tty.print(line.strip("\r\n"))

        # TODO: If you add a 0.1s delay here, it sometimes misses a bit of output at the
        #       end.  Could be related to pexpect/pexpect#120 or
        #       https://pexpect.readthedocs.io/en/stable/commonissues.html#truncated-output-just-before-child-exits  # noqa: B950

    # TODO: Only add newline when necessary
    print()

    pdflatex.close()
    if pdflatex.exitstatus != 0:
        sys.exit(pdflatex.exitstatus)


def print_latexmkrc(cmd, force=False):
    """Print latexmk configuration for using QuieTeX."""
    template = pkg_resources.read_text("quietex", "latexmkrc")
    if cmd.endswith("__main__.py"):
        cmd = "python3 -m " + __package__
    print(template % dict(force=("force" if force else 0), cmd=cmd))


def print_usage():
    """Print usage message."""
    print(
        textwrap.dedent(
            """
        Usage: quietex [OPTIONS] [LATEX] [LATEX-OPTION]... [LATEX-ARGS]

        Filter and colour output of pdflatex.

        optional arguments:
          -h, --help            show this help message and exit
          -q, --quiet           filter out as much output as possible (not just dim)
          -l, --latexmkrc       print latexmkrc
          --latexmkrc-force     print latexmkrc which doesn't check $pdflatex first
        """
        ).strip()
    )


def main(args=None):
    """Handle command line arguments."""
    # Can't use argparse as it chokes on unrecognised options, so parse args manually
    if args is None:
        args = sys.argv
    if len(args) < 2:
        print_usage()
        sys.exit(-1)

    cmd, *args = args
    if args[0] in ("-h", "--help"):
        print_usage()
    elif args[0] in ("-l", "--latexmkrc"):
        print_latexmkrc(cmd)
    elif args[0] == "--latexmkrc-force":
        print_latexmkrc(cmd, force=True)
    else:
        quiet = False
        if args[0] in ("-q", "--quiet"):
            quiet = True
            args = args[1:]
        run_command(args, quiet=quiet, bell_on_error=True)
