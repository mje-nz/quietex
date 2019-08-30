"""Parser for LaTeX compiler log output."""

import re
from collections import namedtuple


# TODO: <> for reading images, {} for reading auxiliary files
class Token(namedtuple("Token", ("type", "text", "value"), defaults=("", None))):
    """LaTeX log output token."""

    # Types
    CLOSE_FILE = "close_file"
    ERROR = "error"
    OPEN_FILE = "open_file"
    OTHER = "other"
    PAGE = "page"
    WARNING = "warning"


class LatexLogParser(object):
    """LaTeX log parser.

    Currently stateless, extracts tokens from one line at a time.
    """

    PAGE_REGEX = re.compile(r"\[(\d+)[ \]\{]")
    # Based on https://github.com/olivierverdier/pydflatex/blob/a466693d0184e9b68b4592b829d0272d0aae4e05/pydflatex/latexlogparser.py#L14  # noqa: B950
    OPEN_FILE_REGEX = re.compile(r" ?\((\.?/[^\s(){}]+)")

    def _is_warning(self, line: str):
        if line.startswith("Overfull") or line.startswith("Underfull"):
            return True
        line = line.lower()
        if "warning" in line:
            return True
        return False

    def _parse_open_close(self, line: str):
        tokens = []
        while True:
            if line == "":
                break
            line = line.strip(" ")
            if line[0] == " ":
                line = line[1:]

            open_match = self.OPEN_FILE_REGEX.match(line)
            if open_match:
                # Open file at start of line
                text = open_match.group()
                value = open_match.group(1)
                tokens.append(Token(Token.OPEN_FILE, text, value))
                line = line[open_match.end() :]
                continue

            if line.startswith(")"):
                # Close file at start of line
                tokens.append(Token(Token.CLOSE_FILE, ")"))
                line = line[1:]
                continue

            open_match = self.OPEN_FILE_REGEX.search(line)
            if open_match:
                # Something we don't recognise, then an open file
                other_msg = line[: open_match.start()].strip(" ")
                # Strip any close files off the end
                close_tokens = []
                while other_msg.endswith(")") and other_msg.count(
                    "("
                ) < other_msg.count(")"):
                    close_tokens.append(Token(Token.CLOSE_FILE, ")"))
                    other_msg = other_msg[:-1]
                # Dump the rest as an other
                tokens.append(Token(Token.OTHER, other_msg))
                tokens += close_tokens
                # Leave the open for the next iteration
                line = line[open_match.start() :]
                continue

            # Give up
            tokens.append(Token(Token.OTHER, line))
            break
        return tokens

    def parse_line(self, line: str):
        """Extract tokens from a line of output."""
        tokens = []
        if line.startswith("(") or line.startswith(")"):
            tokens += self._parse_open_close(line)
        elif line.startswith("!"):
            tokens.append(Token(Token.ERROR, line))
        elif self._is_warning(line):
            tokens.append(Token(Token.WARNING, line))
        elif self.PAGE_REGEX.match(line):
            # Add page tokens later
            pass
        else:
            tokens.append(Token(Token.OTHER, line))

        tokens += [
            Token(Token.PAGE, p.group(), p.group(1))
            for p in self.PAGE_REGEX.finditer(line)
        ]
        return tokens
