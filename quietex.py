#!/usr/bin/env python3
"""Filter and colour output of pdflatex.

Usage: quietex.py <latex engine> <options> <file>

Author: Matthew Edwards
Date: July 2019
"""
import os
import sys
import textwrap

import colorama
import pexpect
from colorama import Fore, Style

colorama.init()


def probably_warning(line: str):
    """Check if a line of pdflatex output is (probably) a warning message.
    """
    if line.startswith("Overfull") or line.startswith("Underfull"):
        return True
    line = line.lower()
    if "warning" in line or "missing" in line:
        return True
    if "undefined" in line and "i'll" not in line:
        # Check for "I'll forget about whatever was undefined." in help text
        return True
    return False


def handle_prompt(pdflatex: pexpect.spawn):
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
            user_response = input(Fore.RED + prompt + Style.RESET_ALL)
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


def handle_line(line: str):
    """Evaluate one line of output and print/colour/suppress it."""
    line = line.strip("\r\n")
    if line.startswith("(/") or line.startswith("(./"):
        # Start loading file
        # print(Style.DIM + line + Style.RESET_ALL)
        pass
    elif line.startswith(")"):
        # Finish loading file
        # print(Style.DIM + line + Style.RESET_ALL)
        pass
    elif line.startswith("!"):
        # Error
        print(Style.BRIGHT + Fore.RED + line + Style.RESET_ALL)
    elif probably_warning(line):
        print(Fore.YELLOW + line + Style.RESET_ALL)
    else:
        print(line)


def run_command(cmd: list):
    """Run the command, filtering and colouring its output.

    The command is assumed to be a pdflatex invocation, but other LaTeX compilers
    probably work too.

    Args:
        cmd (list[str]): Command to run.
    """

    # Disable pdflatex line wrap (where possible)
    env = dict(os.environ, max_print_line="1000000000")

    # Run pdflatex and filter/colour output
    pdflatex = pexpect.spawn(cmd[0], cmd[1:], env=env, encoding="utf-8", timeout=0.2)
    while True:
        try:
            line = pdflatex.readline()
        except pexpect.exceptions.TIMEOUT:
            # Check if it's waiting for input
            handle_prompt(pdflatex)
            continue
        if line == "":
            # EOF
            break
        handle_line(line)

    pdflatex.close()
    sys.exit(pdflatex.exitstatus)


def print_usage():
    print(
        textwrap.dedent(
        """
        Usage: quietex [-h|--help] [LATEX] [OPTION]... [ARGS]

        Filter and colour output of pdflatex.

        optional arguments:
          -h, --help  show this help message and exit
        """
        ).strip()
    )


def main():
    # Can't use argparse as it chokes on unrecognised options, so parse args manually
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(-1)

    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        print_usage()
        return

    run_command(args)


if __name__ == "__main__":
    main()
