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
    cmd = sys.argv[0]
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
        quiet = False
        if args[0] in ("-q", "--quiet"):
            quiet = True
            args = args[1:]
        run_command(args, quiet=quiet)


if __name__ == "__main__":
    main()
