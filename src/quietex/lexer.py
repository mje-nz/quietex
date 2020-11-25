"""Pygments lexer for LaTeX compiler log output."""
import re
from typing import Any, List, Tuple

from pygments.lexer import RegexLexer, default, include
from pygments.token import Generic, Text

__all__ = ["LatexLogLexer", "lex", "split"]

# Tokens
IO = Generic.IO
State = Generic.State  # pylint: disable=C0103
UI = Generic.UI
__all__ += ["Generic", "IO", "UI", "State", "Text"]


class LatexLogLexer(RegexLexer):
    """Lexer for a single line (or section thereof) of LaTeX compiler log output."""

    name = "LatexLog"

    START_PAGE_RE = r"\[\d+\s?"
    OPEN_FILE_RE = r"\(\.?/[^\s(){}]+"

    def __init__(self, ensurenl=False, **options):
        super().__init__(ensurenl=ensurenl, **options)

    def text_and_close_files(self, match):
        """Callback to lex text followed by close-files."""
        tokens = []
        text = match.group()
        if text.count("(") != text.count(")"):
            # Split trailing spaces into a separate token
            # TODO: use bygroups for this instead?
            text_stripped = text.rstrip(" ")
            if text_stripped != text:
                start = len(text_stripped)
                tokens.append((match.start() + start, Text, text[start:]))
                text = text_stripped

            # Split trailing close-files into separate tokens
            while text.endswith(")") and text.count("(") < text.count(")"):
                text = text[:-1]
                tokens.insert(0, (match.start() + len(text), IO.CloseFile, ")"))
        if text:
            tokens.insert(0, (0, Text, text))
        return tokens

    tokens = {
        "inputs": [
            (r"{\.?/[^\s(){}]+}", IO.ReadAux),
            (r"<\.?/[^\s(){}]+(?: \(.*\))?>", IO.ReadImage),
            # TODO: reading fonts
            # (/texlive/mt-msb.cfg)<<ot1tt.cmap>> (./tex/document.tex
            # TODO: reading subsetted fonts, the same but with <filename>
        ],
        "root": [
            # These regexes are acting on the output *after* it's been split into
            # sections that end on a start-page or open-file.
            (r"!.+", Generic.Error),
            (r"^(Overfull|Underfull|.*([Ww]arning|ATTENTION)).*", Generic.Warning),
            (START_PAGE_RE, State.StartPage, "page"),
            (OPEN_FILE_RE, IO.OpenFile, "file"),
            (r"\s*\)", IO.CloseFile, "file"),
            include("inputs"),
            (r".+", text_and_close_files),
        ],
        "page": [
            # Page numbers can also look like [1 <./file>] or [1 {./file}]
            include("inputs"),
            (r"\]", State.EndPage, "#pop"),
        ],
        "file": [
            # After seeing "(/filename" or ")", there can be:
            #   * a space and then another open file, or
            #   * a close file, start page, etc., or
            #   * Arbitrary text from package imports, which might end in a close file.
            # The section we're working on is already split at start-pages and
            # open-files, so let's assume anything following is text and close-files.
            (r"\)", IO.CloseFile),
            default("#pop"),
        ],
    }


class Splitter:
    """Utility class for splitting lines of log output."""

    # TODO: roll this into the lexer?

    PAGE_RE = re.compile(LatexLogLexer.START_PAGE_RE)
    FILE_RE = re.compile(LatexLogLexer.OPEN_FILE_RE)

    @staticmethod
    def split_on_re(regex, value):
        """Split a string into sections starting with a given regex."""
        last_index = 0
        for match in regex.finditer(value):
            section = value[last_index : match.start()]
            if section:
                yield section
                last_index = match.start()
        section = value[last_index:]
        if section:
            yield section

    @classmethod
    def split_on_pages(cls, line):
        """Split a line of output into sections starting with a page number."""
        return cls.split_on_re(cls.PAGE_RE, line)

    @classmethod
    def split_on_io(cls, line):
        """Split a line of output into sections starting with a file opening."""
        return cls.split_on_re(cls.FILE_RE, line)

    @classmethod
    def split(cls, line):
        """Split a line of output by start-page or file-open.

        Yields:
            List[str]: sections of the line, each (other than the first) starting with a
            start-page or file-open.
        """
        for section in cls.split_on_pages(line):
            for section_ in cls.split_on_io(section):
                yield section_


def split(line) -> List[str]:
    """Split a line of output by start-page or file-open.

    Returns:
        List[str]: sections of the line, each (other than the first) starting with a
        start-page or file-open.
    """
    return list(Splitter.split(line))


def _lex(line: str, lexer: LatexLogLexer):
    """Lex a single line of output.

    Yields: (tokentype, value)
    """
    for section in Splitter.split(line):
        for token in lexer.get_tokens(section):
            yield token


def lex(line: str, lexer: LatexLogLexer = None) -> List[Tuple[Any, str]]:
    """Lex a single line of output.

    Returns: list of (tokentype, value)
    """
    if not lexer:
        lexer = LatexLogLexer()
    return list(_lex(line, lexer))
