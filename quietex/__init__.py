#!/usr/bin/env python3
"""Filter and colour output of pdflatex.

Usage: quietex.py <latex engine> <options> <file>

Author: Matthew Edwards
Date: July 2019
"""
import os
import sys
from typing import List

import colorama
import pexpect
from colorama import Fore, Style

from ._meta import __version__  # noqa: F401
from .formatting import LatexLogFormatter
from .frontend import BasicFrontend, TerminalFrontend  # noqa: F401
from .parsing import LatexLogParser

colorama.init()


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
            user_response = tty.input(prompt, style=Fore.RED)
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


def run_command(cmd: List[str], quiet=True):
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

    tty = TerminalFrontend()
    # tty = BasicIo()
    tty.status_style = Fore.BLUE
    tty.print("QuieTeX enabled", style=Style.DIM)

    parser = LatexLogParser()
    formatter = LatexLogFormatter(quiet=quiet)

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
        output = formatter.process_tokens(parser.parse_line(line.strip("\r\n")))
        tty.file = formatter.file
        tty.page = formatter.page
        tty.print(output)

        # TODO: If you add a 0.1s delay here, it sometimes misses a bit of output at the
        #       end.  Could be related to pexpect/pexpect#120 or
        #       https://pexpect.readthedocs.io/en/stable/commonissues.html#truncated-output-just-before-child-exits  # noqa: B950

    # TODO: Only add newline when necessary
    print()

    pdflatex.close()
    sys.exit(pdflatex.exitstatus)
