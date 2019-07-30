#!/usr/bin/env python3
"""Filter output of pdflatex.

Usage: filter.py <latex engine> <options> <file>

Author: Matthew Edwards
Date: July 2019
"""
import os
import pexpect
import sys

import colorama
from colorama import Fore, Style
colorama.init()


def main(cmd):
    # Disable pdflatex line wrap (where possible)
    env = dict(os.environ, max_print_line="1000000000")

    # Run pdflatex and filter/colour output
    pdflatex = pexpect.spawn(cmd[0], cmd[1:], env=env, encoding='utf-8')
    while True:
        line = pdflatex.readline()
        if line == '':
            # EOF
            break
        line = line.strip('\r\n')
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
