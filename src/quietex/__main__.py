#!/usr/bin/env python3
"""Filter and colour output of pdflatex.

Usage: quietex.py <latex engine> <options> <file>

Author: Matthew Edwards
Date: July 2019
"""
import importlib.resources as pkg_resources
import sys
import textwrap

from . import run_command


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


if __name__ == "__main__":
    main()
