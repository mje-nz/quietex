"""Main program implementation."""
import argparse
import importlib.resources as pkg_resources
import os
import sys
from typing import List

import pexpect

from ._meta import __version__  # noqa: F401
from .frontend import BasicFrontend, TerminalFrontend


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
        #       https://pexpect.readthedocs.io/en/stable/commonissues.html#truncated-output-just-before-child-exits

    # TODO: Only add newline when necessary
    print()

    pdflatex.close()
    if pdflatex.exitstatus != 0:
        sys.exit(pdflatex.exitstatus)


def print_latexmkrc(cmd, force=False):
    """Print latexmk configuration for using QuieTeX."""
    template = pkg_resources.read_text("quietex", "latexmkrc")
    start, no_force_clause, force_clause, end = template.split("# <split>\n")
    print(start, end="")
    if force:
        print(force_clause % dict(cmd=cmd), end="")
    else:
        print(no_force_clause % dict(cmd=cmd), end="")
    print(end, end="")


def split_argv(argv: List[str]):
    """Split argument list into quietex invocation, quietex args, and command to run."""
    quietex_command, *argv = argv
    if "__main__" in quietex_command:
        # argv[0] is the path to __main__.py when `python -m quietex` runs
        quietex_command = "python -m quietex"
    try:
        # Split argument list before the first non-option argument
        first_arg_index = next(i for i, a in enumerate(argv) if not a.startswith("-"))
        quietex_argv = argv[:first_arg_index]
        cmd = argv[first_arg_index:]
        return quietex_command, quietex_argv, cmd
    except StopIteration:
        return quietex_command, argv, None


def parse_args(argv: List[str], command):
    """Parse quietex command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Filter and colourize LaTeX compilation output."
    )
    parser.add_argument("pdflatex", nargs="?", help="the command to run, e.g. pdflatex")
    parser.add_argument("args", nargs="*", help="the command's arguments")
    parser.add_argument(
        "--latexmkrc",
        action="store_true",
        help="print latexmk settings which enable QuieTeX and also colourize latexmk "
        "output; include `eval quietex --latexmkrc` in latexmkrc to use",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="when printing latexmk settings, enable quietex even if $pdflatex is "
        "non-default",
    )
    bell = parser.add_mutually_exclusive_group()
    bell.add_argument(
        "--bell", "-b", action="store_true", help="ring bell on LaTeX error (default)"
    )
    bell.add_argument(
        "--no-bell",
        action="store_false",
        dest="bell",
        help="don't ring bell on LaTeX error",
    )
    quiet = parser.add_mutually_exclusive_group()
    quiet.add_argument(
        "--quiet", "-q", action="store_true", help="hide I/O messages (default)"
    )
    quiet.add_argument(
        "--verbose",
        "-v",
        action="store_false",
        dest="quiet",
        help="just dim I/O messages, and also add information messages from QuieTeX",
    )
    parser.set_defaults(quiet=True, bell=True)
    args = parser.parse_args(argv)

    # Easier to check these manually than to explain it to argparse
    if args.latexmkrc and command:
        print("Use --latexmkrc or command, not both\n")
    elif args.force and command:
        print("--force is only valid with --latexmkrc\n")
    elif not args.latexmkrc and not command:
        pass
    else:
        return args
    # Hit one of the error cases
    parser.print_help()
    sys.exit(1)


def main(argv=None):
    """Handle command line arguments."""
    if argv is None:
        argv = sys.argv

    quietex_command, quietex_argv, command = split_argv(argv)
    args = parse_args(quietex_argv, command)

    if args.latexmkrc:
        if not args.quiet:
            quietex_command += " --verbose"
        if not args.bell:
            quietex_command += " --no-bell"
        print_latexmkrc(quietex_command, args.force)
    else:
        run_command(command, quiet=args.quiet, bell_on_error=args.bell)
