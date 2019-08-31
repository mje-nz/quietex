"""Formatting logic for QuieTeX output."""

from typing import List

from colorama import Fore, Style

from .input_output import BasicIo
from .tokens import *  # noqa: F403


class LatexLogFormatter(object):
    """Formatter for QuieTeX output."""

    def __init__(self, quiet=True):
        self.quiet = quiet
        self.stack = []

    def process_tokens(self, tty: BasicIo, tokens: List[Token]):
        """Process a list of tokens."""
        for token in tokens:
            if type(token) is PageToken:
                tty.page = token.value
            elif type(token) is OpenFileToken:
                self.stack.append(token.value)
                tty.file = token.value
            elif type(token) is CloseFileToken:
                try:
                    self.stack.pop()
                    tty.file = self.stack[-1]
                except IndexError:
                    tty.file = None

    def print_tokens(self, tty: BasicIo, tokens: List[Token]):
        """Print (if appropriate) a list of tokens representing one line."""
        for token in tokens:
            value = token.text
            style = None
            if type(token) is ErrorToken:
                style = Style.BRIGHT + Fore.RED
            elif type(token) is WarningToken:
                style = Fore.YELLOW
            elif type(token) in [OpenFileToken, CloseFileToken]:
                if self.quiet:
                    continue
                value = token.text
                style = Style.DIM
            tty.print(value, style=style, end="")
        # End line
        tty.print()

    def handle_tokens(self, tty: BasicIo, tokens: List[Token]):
        """Process and print (if appropriate) a list of tokens representing one line."""
        self.process_tokens(tty, tokens)
        self.print_tokens(tty, tokens)
