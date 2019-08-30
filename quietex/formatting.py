"""Formatting logic for QuieTeX output."""

from typing import List

from colorama import Fore, Style

from .input_output import BasicIo
from .parsing import Token


class LatexLogFormatter(object):
    """Formatter for QuieTeX output."""

    def __init__(self, quiet=True):
        self.quiet = quiet
        self.stack = []

    def process_tokens(self, tty: BasicIo, tokens: List[Token]):
        """Process a list of tokens."""
        for token in tokens:
            if token.type == Token.PAGE:
                tty.page = token.value
            elif token.type == Token.OPEN_FILE:
                self.stack.append(token.value)
                tty.file = token.value
            elif token.type == Token.CLOSE_FILE:
                try:
                    self.stack.pop()
                    tty.file = self.stack[-1]
                except IndexError:
                    tty.file = None

    def print_tokens(self, tty: BasicIo, tokens: List[Token]):
        """Print (if appropriate) a list of tokens representing one line."""
        have_printed = False
        for token in tokens:
            value = token.text
            style = None
            if token.type == Token.ERROR:
                style = Style.BRIGHT + Fore.RED
            elif token.type == Token.WARNING:
                style = Fore.YELLOW
            elif token.type in [Token.OPEN_FILE, Token.CLOSE_FILE, Token.PAGE]:
                # TODO: Option for dim
                if self.quiet:
                    continue
                value = token.text
            tty.print(value, style=style)
            have_printed = True
        if not have_printed:
            # Didn't print anything, make sure the status line is updated
            tty.print("", end="")

    def handle_tokens(self, tty: BasicIo, tokens: List[Token]):
        """Process and print (if appropriate) a list of tokens representing one line."""
        self.process_tokens(tty, tokens)
        self.print_tokens(tty, tokens)
