"""Tokens for LaTeX log output parser."""

from attr import attrib, attrs


# TODO: {} for reading auxiliary files
@attrs
class Token(object):
    """LaTeX log output token."""

    text: str = attrib()
    value: str = attrib(default=None)


class CloseFileToken(Token):  # noqa: D101
    __slots__ = ()

    def __init__(self):
        super().__init__(")")


class ErrorToken(Token):  # noqa: D101
    __slots__ = ()

    def __init__(self, text):
        super().__init__(text)


class NewlineToken(Token):  # noqa: D101
    __slots__ = ()

    def __init__(self):
        super().__init__("\n")


class OpenFileToken(Token):
    """Open file token.

    Attributes:
        text: Full text of token including ( and preceding whitespace
        value: File being opened.
    """

    __slots__ = ()


class OtherToken(Token):
    """Any message that isn't classified as something else."""

    __slots__ = ()

    def __init__(self, text):
        super().__init__(text)


class PageToken(Token):
    """Page number token (emitted at the start of a new page).

    Note that the end of a page number message can get mixed up in other messages.

    Attributes:
        text: Full text of token including [ and preceding whitespace
        value: Page number.
    """

    __slots__ = ()


class ReadAuxToken(Token):
    """Read subfont or map file token."""

    __slots__ = ()

    def __init__(self, text):
        super().__init__(text)


class ReadImageToken(Token):
    """Read image or font token.

    Never contains other tokens, sometimes contains output from the image loader.
    """

    __slots__ = ()

    def __init__(self, text):
        super().__init__(text)


class WarningToken(Token):  # noqa: D101
    __slots__ = ()

    def __init__(self, text):
        super().__init__(text)
