#!/usr/bin/env python3
"""Filter and colour output of pdflatex.

Usage: quietex.py <latex engine> <options> <file>

Author: Matthew Edwards
Date: July 2019
"""
import os
import re
import sys
import textwrap

import colorama
import pexpect
from colorama import Fore, Style

colorama.init()


def probably_warning(line: str):
    """Check if a line of pdflatex output is (probably) a warning message."""
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



page_number_regex = re.compile(r"\[(\d+)[ \]\{]")
def find_page_number(line: str):
    pages = page_number_regex.findall(line)
    if pages:
        return pages[-1]


# Based on https://github.com/olivierverdier/pydflatex/blob/a466693d0184e9b68b4592b829d0272d0aae4e05/pydflatex/latexlogparser.py#L14
file_regex = re.compile(r"\((\.?/[^\s(){}]+)")
def find_file(line: str):
    files = file_regex.findall(line)
    if files:
        return files[-1]


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
    elif page_number_regex.match(line):
        # Page number
        # print(Style.DIM + line + Style.RESET_ALL)
        pass
    elif line.startswith("!"):
        # Error
        print(Style.BRIGHT + Fore.RED + line + Style.RESET_ALL)
    elif probably_warning(line):
        print(Fore.YELLOW + line + Style.RESET_ALL)
    else:
        print(line)


def delete_last_line_printed():
    # Cursor to start of line
    sys.stdout.write("\x1b[G")
    # Delete whole line
    sys.stdout.write("\x1b[2K")
    # sys.stdout.write(".")


def print_status(last_page, last_file):
    status = f"[{last_page}]"
    if last_file:
        status += f" ({last_file})"
    print(Fore.BLUE + status + Style.RESET_ALL, end="", flush=True)


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
    print(Style.DIM + "QuieTeX enabled" + Style.RESET_ALL)
    print()  # Hack to avoid losing this line at the start of the loop
    last_page = 0
    last_file = ""

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

        delete_last_line_printed()

        handle_line(line)

        # TODO: This kind of works, but it would be better if it parsed the line bit by bit
        page_number = find_page_number(line)
        if page_number:
            last_page = page_number

        # TODO: This doesn't really work as intended, it needs to track the whole stack
        file = find_file(line)
        if file:
            last_file = file

        print_status(last_page, last_file)
        if page_number:
            # When the page number changes, print an extra status so it stays in the output
            print()
            print_status(last_page, last_file)

    pdflatex.close()
    sys.exit(pdflatex.exitstatus)


latexmkrc_template = r"""
use Term::ANSIColor;

# Make pdflatex output prettier with QuieTeX
if (%r or rindex($pdflatex, "pdflatex", 0) == 0) {
    $pdflatex = "%s $pdflatex";
} else {
    # $pdflatex doesn't start with "pdflatex", which means there's some other
    # customisation in latexmkrc already
    my $msg1 = '$pdflatex not recognised so QuieTeX will not be used.';
    my $msg2 = 'To override this check, use quietex --latexmkrc-force';
    if (-t STDERR) {
        # Only use color if a terminal is attached
        print STDERR colored($msg1, 'yellow'), "\n";
        print STDERR colored($msg2, 'yellow'), "\n";
    } else {
        print STDERR $msg1, "\n", $msg2, "\n";
    }
}

# Colour "Running pdflatex" etc messages
{
    no warnings 'redefine';
    my $old_warn_running = \&main::warn_running;
    sub color_warn_running {
        print STDERR color('green');
        $old_warn_running->(@_);
        print STDERR color('reset');
    }
    if (-t STDERR) {
        # Only use color if a terminal is attached
        *main::warn_running = \&color_warn_running;
    }
}
"""


def print_latexmkrc(force=False):
    """Print latexmk configuration for using QuieTeX."""
    print(latexmkrc_template % ("force" if force else 0, sys.argv[0]))


def print_usage():
    """Print usage message."""
    print(
        textwrap.dedent(
            """
        Usage: quietex [OPTIONS] [LATEX] [LATEX-OPTION]... [LATEX-ARGS]

        Filter and colour output of pdflatex.

        optional arguments:
          -h, --help            show this help message and exit
          -l, --latexmkrc       print latexmkrc
          --latexmkrc-force     print latexmkrc which doesn't check $pdflatex first
        """
        ).strip()
    )


def main():
    """Handle command line arguments."""
    # Can't use argparse as it chokes on unrecognised options, so parse args manually
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(-1)

    args = sys.argv[1:]
    if args[0] in ("-h", "--help"):
        print_usage()
    elif args[0] in ("-l", "--latexmkrc"):
        print_latexmkrc()
    elif args[0] == "--latexmkrc-force":
        print_latexmkrc(force=True)
    else:
        run_command(args)


if __name__ == "__main__":
    main()
