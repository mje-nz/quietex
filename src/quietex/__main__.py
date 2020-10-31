#!/usr/bin/env python3
"""Filter and colour output of pdflatex.

Usage: quietex.py <latex engine> <options> <file>

Author: Matthew Edwards
Date: July 2019
"""
import sys
import textwrap

from . import run_command

LATEXMKRC_TEMPLATE = r"""
use Term::ANSIColor;

# Make pdflatex output prettier with QuieTeX
if (%r or rindex($pdflatex, "pdflatex", 0) == 0) {
    $pdflatex = "%s $pdflatex";
} else {
    # $pdflatex doesn't start with "pdflatex", which means there's some other
    # customisation in latexmkrc already
    my $msg = 'It looks like $pdflatex is already customized in your latexmkrc, so ' .
        'QuieTeX will not insert itself.  To override this check, use ' .
        '`quietex --latexmkrc-force`.';
    if (-t STDERR) {
        # Only use color if a terminal is attached
        $msg = colored($msg, 'yellow')
    }
    print STDERR $msg, "\n";
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


def print_latexmkrc(cmd, force=False):
    """Print latexmk configuration for using QuieTeX."""
    if cmd.endswith("__main__.py"):
        cmd = "python3 -m " + __package__
    print(LATEXMKRC_TEMPLATE % ("force" if force else 0, cmd))


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
