"""Parser for LaTeX compiler log output."""

import re
from collections import namedtuple


# TODO: <> for reading images, {} for reading auxiliary files
# TODO: having this a tuple makes it easy to mess up (it really shouldn't be a sequence)
class Token(namedtuple("Token", ("type", "text", "value"), defaults=("", None))):
    """LaTeX log output token."""

    # Types
    CLOSE_FILE = "close"
    ERROR = "error"
    OPEN_FILE = "open"
    OTHER = "other"
    PAGE = "page"
    WARNING = "warning"
    NEWLINE = "newline"


class LatexLogParser(object):
    """LaTeX log parser.

    Currently stateless, extracts tokens from one line at a time.
    """

    PAGE_REGEX = re.compile(r" ?\[(\d+)[ \]]?")
    # Based on https://github.com/olivierverdier/pydflatex/blob/a466693d0184e9b68b4592b829d0272d0aae4e05/pydflatex/latexlogparser.py#L14  # noqa: B950
    OPEN_FILE_REGEX = re.compile(r" ?\((\.?/[^\s(){}]+)")

    def _is_warning(self, line: str):
        if line.startswith("Overfull") or line.startswith("Underfull"):
            return True
        line = line.lower()
        if "warning" in line:
            return True
        return False

    def _parse_error_or_warning(self, line):
        if line.startswith("!"):
            return Token(Token.ERROR, line)
        elif self._is_warning(line):
            return Token(Token.WARNING, line)

    def _search_for_token(self, text: str):
        """Find the next token in the text.

        Only open file and page number tokens can appear at the end of other messages.

        Returns: re.Match instance or None
        """
        matches = []
        open_match = self.OPEN_FILE_REGEX.search(text)
        if open_match:
            matches.append(open_match)
        page_match = self.PAGE_REGEX.search(text)
        if page_match:
            matches.append(page_match)
        if not matches:
            return
        matches.sort(key=lambda m: m.start())
        return matches[0]

    def _parse_partial(self, text: str):
        """Split as much of `text` as possible into tokens.

        Returns:
            list[Token], str: The tokens and whatever's left at the end.
        """
        tokens = []
        while True:
            if text == "":
                break

            open_match = self.OPEN_FILE_REGEX.match(text)
            if open_match:
                # Open file at start of text
                tokens.append(
                    Token(Token.OPEN_FILE, open_match.group(), open_match.group(1))
                )
                text = text[open_match.end() :]
                continue

            if text.startswith(")"):
                # Close file at start of text
                tokens.append(Token(Token.CLOSE_FILE, ")"))
                text = text[1:]
                continue

            page_match = self.PAGE_REGEX.match(text)
            if page_match:
                # Page number at start of text
                tokens.append(
                    Token(Token.PAGE, page_match.group(), page_match.group(1))
                )
                text = text[page_match.end() :]
                continue

            match = self._search_for_token(text)
            if match:
                # Something we don't recognise, then an open file or page number
                other_msg = text[: match.start()]
                # If there's an other message mixed in with open/close messages, it
                # must come from a package so should be between an open and a close, so
                # we need to work backwards and get the close.  If there are parentheses
                # inside the message, assume they're balanced.
                close_tokens = []
                while other_msg.endswith(")") and other_msg.count(
                    "("
                ) < other_msg.count(")"):
                    close_tokens.append(Token(Token.CLOSE_FILE, ")"))
                    other_msg = other_msg[:-1]
                # Dump the rest as an other
                tokens.append(Token(Token.OTHER, other_msg))
                tokens += close_tokens
                # Leave the open/page for the next iteration
                text = text[match.start() :]
                continue

            if text.endswith(")"):
                # TODO: dedupe
                # Strip close tokens off the end
                close_tokens = []
                while text.endswith(")") and text.count("(") < text.count(")"):
                    close_tokens.append(Token(Token.CLOSE_FILE, ")"))
                    text = text[:-1]
                # Dump the rest as an other
                tokens.append(Token(Token.OTHER, text))
                tokens += close_tokens
                text = ""

            # Give up
            break
        return tokens, text

    def parse_line(self, line: str):
        """Extract tokens from a line of output.

        `line` should not end with a newline, and a newline token will not be returned.

        Returns:
            list[Token]: The tokens found in the line.
        """
        tokens = []

        # First check for page numbers
        # TODO: Are page numbers the only things that can appear after a warning
        #   without a newline?
        # If there's a page number, only look at the first part of the line
        error_line = line
        page_match = self.PAGE_REGEX.search(line)
        if page_match:
            error_line = line[: page_match.start()]
        # Try parsing the line as an error or warning
        error_token = self._parse_error_or_warning(error_line)
        if error_token:
            tokens.append(error_token)
            line = line[len(error_line) :]

        # Try parsing the rest of the ine
        parsed_tokens, remaining_text = self._parse_partial(line)
        tokens += parsed_tokens

        # Give up
        if remaining_text:
            tokens += [Token(Token.OTHER, remaining_text)]

        return tokens

    def parse_text(self, text: str):
        """Parse a block of text (including newlines)."""
        tokens = []
        for line in text.splitlines():
            tokens += self.parse_line(line)
            tokens += [Token(Token.NEWLINE, "\n")]
        return tokens
