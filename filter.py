#!/usr/bin/env python3
"""Filter output of pdflatex.

Usage: filter.py <latex engine> <options> <file>

Author: Matthew Edwards
Date: July 2019
"""
import os
import subprocess
import sys

import colorama
from colorama import Fore, Style
colorama.init()


def main(cmd):
    # Disable pdflatex line wrap (where possible)
    env = dict(os.environ, max_print_line="1000000000")

    # Run pdflatex and filter/colour output
    pdflatex = subprocess.Popen(
        cmd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    for line in iter(pdflatex.stdout.readline, b''):
        line = line.decode('utf8').strip()
        if line.startswith('(/') or line.startswith('(./'):
            # Start loading file
            #print(Style.DIM + line + Style.RESET_ALL)
            pass
        elif line.startswith(')'):
            # Finish loading file
            #print(Style.DIM + line + Style.RESET_ALL)
            pass
        elif line.startswith('!'):
            # Error
            print(Style.BRIGHT + Fore.RED + line + Style.RESET_ALL)
        elif line.startswith('Overfull') or line.startswith('Underfull') \
                or 'warning' in line.lower() or 'missing' in line.lower() or \
                'undefined' in line.lower():
            # Warning
            print(Fore.YELLOW + line + Style.RESET_ALL)
        else:
            print(line)

    # TODO: Handle input prompt when there's an error


if __name__ == '__main__':
    assert len(sys.argv) > 1
    main(sys.argv[1:])
