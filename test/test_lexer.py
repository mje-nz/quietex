"""Tests for lexer module."""
from pathlib import Path
from typing import Any, List, Tuple

import pytest

from quietex.lexer import IO, Generic, State, Text, lex, split


def test_split():
    """Test splitting lines by start-page and open-file."""
    msg = [
        r"(/usr/local/texlive/2019/texmf-dist/tex/latex/lm/ot1lmtt.fd) ",
        "[1{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}] ",
        "[2] ",
        "(./Thesis.toc) ",
        "[3]",
    ]
    # TODO: more thorough test cases
    assert list(split("".join(msg))) == msg


def combine_text(tokens):
    """Combine consecutive Text tokens."""
    # TODO: TokenMergeFilter?
    out: List[Tuple[Any, str]] = []
    for (tokentype, value) in tokens:
        if tokentype == Text and out and out[-1][0] == Text:
            out[-1] = (tokentype, out[-1][1] + value)
        else:
            out.append((tokentype, value))
    return out


def test_combine_text():
    """Test combine_text helper function."""
    tokens = [(Text, "a"), (Text, "b"), (IO, "c"), ("Text", "d")]
    assert combine_text(tokens) == [(Text, "ab"), (IO, "c"), ("Text", "d")]


# Output from a simple test document:
# This is pdfTeX, Version 3.14159265-2.6-1.40.20 (TeX Live 2019) (preloaded format=pdflatex)  # noqa: B950
#  restricted \write18 enabled.
# entering extended mode
# (./test.tex
# LaTeX2e <2018-12-01>
# (/usr/local/texlive/2019/texmf-dist/tex/latex/base/article.cls
# Document Class: article 2018/09/03 v1.4i Standard LaTeX document class
# (/usr/local/texlive/2019/texmf-dist/tex/latex/base/size10.clo)) (./test.aux)
# (./include file.tex) [1{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}] (./test.aux) )</usr/local/texlive/2019/texmf-dist/fonts/type1/public/amsfonts/cm/cmr10.pfb>  # noqa: B950
# Output written on test.pdf (1 page, 12659 bytes).
# Transcript written on test.log.


@pytest.mark.parametrize(
    "msg",
    (
        "This is pdfTeX, Version 3.14159265-2.6-1.40.20 (TeX Live 2019) (preloaded "
        "format=pdflatex)",
        r" restricted \write18 enabled.",
        "LaTeX2e <2018-12-01>",
        "Document Class: article 2018/09/03 v1.4i Standard LaTeX document class",
        "Output written on test.pdf (1 page, 12659 bytes).",
        "Transcript written on test.log.",
    ),
)
def test_lex_text(msg):
    """Test lexing some uninteresting log messages."""
    assert combine_text(lex(msg)) == [(Text, msg)]


@pytest.mark.parametrize(
    "msg",
    ("(./test.tex", "(/usr/local/texlive/2019/texmf-dist/tex/latex/base/article.cls"),
)
def test_lex_file_opening_simple(msg):
    """Test lexing some simple file open messages."""
    assert lex(msg) == [(IO.OpenFile, msg.strip())]


@pytest.mark.parametrize("msg", (")", " )"))
def test_lex_file_closing_simple(msg):
    """Test lexing the simplest file close message."""
    assert lex(msg) == [(IO.CloseFile, msg)]


def test_lex_open_close_file():
    """Test lexing an open file message followed by a close file message."""
    assert lex("(./test.tex)") == [(IO.OpenFile, "(./test.tex"), (IO.CloseFile, ")")]


def test_lex_files_complex():
    """Test lexing many open/close file messages on one line."""
    msg = ")) (/usr/a) (/usr/b (/usr/c (/usr/d)) (/usr/e) (/usr/f)) (/usr/g (/usr/h))"
    assert lex(msg) == [
        (IO.CloseFile, ")"),
        (IO.CloseFile, ")"),
        (Text, " "),
        (IO.OpenFile, "(/usr/a"),
        (IO.CloseFile, ")"),
        (Text, " "),
        (IO.OpenFile, "(/usr/b"),
        (Text, " "),
        (IO.OpenFile, "(/usr/c"),
        (Text, " "),
        (IO.OpenFile, "(/usr/d"),
        (IO.CloseFile, ")"),
        (IO.CloseFile, ")"),
        (Text, " "),
        (IO.OpenFile, "(/usr/e"),
        (IO.CloseFile, ")"),
        (Text, " "),
        (IO.OpenFile, "(/usr/f"),
        (IO.CloseFile, ")"),
        (IO.CloseFile, ")"),
        (Text, " "),
        (IO.OpenFile, "(/usr/g"),
        (Text, " "),
        (IO.OpenFile, "(/usr/h"),
        (IO.CloseFile, ")"),
        (IO.CloseFile, ")"),
    ]


def test_lex_message_inside_files():
    """Test lexing a message hidden amongst open/close file messages."""
    msg = [
        "(/usr/local/texlive/2019/texmf-dist/tex/latex/fp/fp.sty",
        " `Fixed Point Package', Version 0.8, April 2, 1995 (C) Michael Mehlich ",
        "(/usr/local/texlive/2019/texmf-dist/tex/latex/fp/defpattern.sty",
        ")",
    ]
    assert combine_text(lex("".join(msg))) == [
        (IO.OpenFile, msg[0]),
        (Text, msg[1]),
        (IO.OpenFile, msg[2]),
        (IO.CloseFile, msg[3]),
    ]


@pytest.mark.parametrize(
    "msg",
    (
        (
            (
                "(/usr/local/texlive/2019/texmf-dist/tex/latex/fp/fp.sty",
                " `Fixed Point Package', Version 0.8, April 2, 1995 (C) Michael Mehlich",
                ")",
                " ",
                "(/usr/local/texlive/2019/texmf-dist/tex/latex/fp/defpattern.sty",
                ")",
            ),
            (
                "(/usr/local/texlive/2019/texmf-dist/tex/latex/lineno/lineno.sty",
                " Style option: `fancyvrb' v3.2a <2019/01/15> (tvz)",
                ")",
                " ",
                "(/usr/local/texlive/2019/texmf-dist/tex/latex/upquote/upquote.sty",
                ")",
            ),
        )
    ),
)
def test_lex_message_followed_by_close(msg):
    """Test lexing a message hidden amongst open/close file messages.

    This is basically the last one but with a CloseFile after the message.
    """
    assert combine_text(lex("".join(msg))) == [
        (IO.OpenFile, msg[0]),
        (Text, msg[1]),
        (IO.CloseFile, ")"),
        (Text, " "),
        (IO.OpenFile, msg[4]),
        (IO.CloseFile, msg[5]),
    ]


def test_lex_message_inside_files_fancyvrb():
    """Test lexing the message from loading fancyvrb, which has brackets in it (!)."""
    msg = [
        "(/usr/local/texlive/2019/texmf-dist/tex/latex/fancyvrb/fancyvrb.sty",
        " Style option: `fancyvrb' v3.2a <2019/01/15> (tvz)",
        ")",
        " ",
        "(/usr/local/texlive/2019/texmf-dist/tex/latex/upquote/upquote.sty",
    ]
    assert lex("".join(msg)) == [
        (IO.OpenFile, msg[0]),
        (Text, msg[1]),
        (IO.CloseFile, msg[2]),
        (Text, msg[3]),
        (IO.OpenFile, msg[4]),
    ]


def test_lex_message_inside_files_fancyvrb_minimal():
    """Test lexing the message from loading fancyvrb, which has brackets in it (!).

    Make sure it works without the next open message.
    """
    msg = [
        "(/usr/local/texlive/2019/texmf-dist/tex/latex/fancyvrb/fancyvrb.sty",
        " Style option: `fancyvrb' v3.2a <2019/01/15> (tvz)",
        ")",
    ]
    assert lex("".join(msg)) == [
        (IO.OpenFile, msg[0]),
        (Text, msg[1]),
        (IO.CloseFile, msg[2]),
    ]


@pytest.mark.parametrize(
    "msg",
    (
        "<./img/test.jpg>",
        "<./img/test.jpg>",
        "<./img/test.png>",
        "<./img/test.png (PNG copy)>",
        "</usr/local/texlive/2019/texmf-dist/fonts/type1/public/lm/lmbx10.pfb>",
        # TODO: Names with spaces
    ),
)
def test_lex_read_image(msg):
    """Test lexing some read images messages"""
    assert lex(msg) == [(IO.ReadImage, msg)]


def test_lex_read_image_in_warning():
    """Test lexing a read image inside a page number at the end of a warning."""
    line = r"Underfull \vbox (badness 7963) has occurred while \output is active [2 <./test.png (PNG copy)>]"  # noqa: B950
    assert lex(line) == [
        (
            Generic.Warning,
            r"Underfull \vbox (badness 7963) has occurred while \output is active ",
        ),
        (State.StartPage, "[2 "),
        (IO.ReadImage, "<./test.png (PNG copy)>"),
        (State.EndPage, "]"),
    ]


@pytest.mark.parametrize(
    "msg",
    (
        "{/usr/local/texlive/2019/texmf-dist/fonts/enc/dvips/lm/lm-mathit.enc}",
        "{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}",
        # TODO: Names with spaces
    ),
)
def test_lex_read_aux(msg):
    """Test lexing some read aux messages"""
    assert lex(msg) == [(IO.ReadAux, msg)]


def test_lex_read_aux_in_page():
    """Test lexing a read aux inside a page number."""
    line = "[1{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}]"
    assert lex(line) == [
        (State.StartPage, "[1"),
        (
            IO.ReadAux,
            "{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}",
        ),
        (State.EndPage, "]"),
    ]


# New output from a simple test document with an error:
# ! Undefined control sequence.
# l.6 \badcommand


def test_lex_error():
    """Test lexing an error message."""
    msg = "! Undefined control sequence."
    assert lex(msg) == [(Generic.Error, msg)]


# A few warnings from a more complicated document
# Underfull \vbox (badness 10000) has occurred while \output is active [19]
# Overfull \hbox (2.79605pt too wide) detected at line 132
# LaTeX Warning: Marginpar on page 7 moved.
# Package natbib Warning: Citation `Siebert2009' on page 17 undefined on input line 22.
# Package microtype Warning: \nonfrenchspacing is active. Adjustment of
# (microtype)                interword spacing will disable it. You might want
# (microtype)                to add `\microtypecontext{spacing=nonfrench}'
# (microtype)                to your preamble.
# pdfTeX warning (dest): name{Hfootnote.2} has been referenced but does not exist, replaced by a fixed one  # noqa: B950


# TODO: Find examples for this old code
#     if "warning" in line or "missing" in line:
#         return True
#     if "undefined" in line and "i'll" not in line:
#         # Check for "I'll forget about whatever was undefined." in help text
#         return True


@pytest.mark.parametrize(
    "msg",
    (
        r"Underfull \vbox (badness 10000) has occurred while \output is active",
        r"Overfull \hbox (2.79605pt too wide) detected at line 132",
        "LaTeX Warning: Marginpar on page 7 moved.",
        "Package natbib Warning: Citation `Siebert2009' on page 17 undefined on input line 22.",  # noqa: B950
        "pdfTeX warning (dest): name{Hfootnote.2} has been referenced but does not exist, replaced by a fixed one",  # noqa: B950
    ),
)
def test_lex_simple_warnings(msg):
    """Test lexing simple warning messages."""
    assert lex(msg) == [(Generic.Warning, msg)]


# A few examples of page numbers and false positives from a complicated document
# [Loading MPS to PDF converter (version 2006.09.02).]
# ) (/usr/local/texlive/2019/texmf-dist/tex/latex/oberdiek/epstopdf-base.sty (/usr/local/texlive/2019/texmf-dist/tex/latex/oberdiek/grfext.sty) (/usr/local/texlive/2019/texmf-dist/tex/latex/latexconfig/epstopdf-sys.cfg)) (/usr/local/texlive/2019/texmf-dist/tex/latex/oberdiek/pdflscape.sty (/usr/local/texlive/2019/texmf-dist/tex/latex/graphics/lscape.sty)) ABD: EveryShipout initializing macros (/usr/local/texlive/2019/texmf-dist/tex/latex/translations/translations-basic-dictionary-english.trsl) (./pythontex-files-Thesis/Thesis.pytxmcr) (./pythontex-files-Thesis/Thesis.pytxpyg) (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/ot1lmr.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/omllmm.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/omslmsy.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/omxlmex.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/amsfonts/umsa.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/microtype/mt-msa.cfg) (/usr/local/texlive/2019/texmf-dist/tex/latex/amsfonts/umsb.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/microtype/mt-msb.cfg) (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/ot1lmss.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/ot1lmtt.fd) [1{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}] [2] (./Thesis.toc) (./Thesis.gls-abr [3] [4]) (./Thesis.sls [5] [6]) [7] [8] (./Thesis.tdo [9]) [10] (./chapters/fiducial_marker_system/fiducial_marker_system.tex  # noqa: B950
# [17 <./chapters/checkerboards//img/checkerboard.pdf>]
# [18]
#  [][][][]
# Underfull \vbox (badness 7963) has occurred while \output is active [2 <./chapters/fiducial_marker_system//img/basic_marker.png (PNG copy)>]  # noqa: B950
# Underfull \vbox (badness 10000) has occurred while \output is active [19]
# \OT1/lmr/bx/n/10.95 H \OT1/lmr/m/n/10.95 = [] [] \OML/lmm/m/it/10.95 :


def test_lex_page_number_simple():
    """Test lexing a simple page number."""
    assert lex("[1]") == [(State.StartPage, "[1"), (State.EndPage, "]")]


@pytest.mark.parametrize(
    "msg",
    (
        "(./Thesis.gls-abr [1])",
        ") (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/ot1lmtt.fd) [1]",
        "[1 <./chapters/fiducial_marker_system//img/basic_marker.png (PNG copy)>]",
        "[1{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}]",
        r"Underfull \vbox (badness 10000) has occurred while \output is active [1]",
        # TODO: [1{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}] [2] (./Thesis.toc)  # noqa: B950
    ),
)
def test_lexing_page_number_complex(msg):
    """Test lexing page numbers on the same line as other messages."""
    tokens = lex(msg)
    page_tokens = [(t, v) for (t, v) in tokens if t == State.StartPage]
    assert len(page_tokens) == 1
    assert page_tokens[0][1].strip("[] ") == "1"


def test_lexing_page_number_complex_1():
    """Test lexing a page number inside an open/close file."""
    assert lex("(./Thesis.gls-abr [1])") == [
        (IO.OpenFile, "(./Thesis.gls-abr"),
        (Text, " "),
        (State.StartPage, "[1"),
        (State.EndPage, "]"),
        (IO.CloseFile, ")"),
    ]


def test_lexing_page_number_complex_2():
    """Test lexing a page number at the end of a warning."""
    msg = r"Underfull \vbox (badness 10000) has occurred while \output is active [1]"
    assert lex(msg) == [
        (Generic.Warning, msg[:-3]),
        (State.StartPage, "[1"),
        (State.EndPage, "]"),
    ]


@pytest.mark.parametrize(
    "msg", ("[Loading MPS to PDF converter (version 2006.09.02).]", " [][][][]")
)
def test_lex_page_number_false_positives(msg):
    """Test lexing things that look like page numbers but aren't."""
    assert lex(msg) == [(Text, msg)]


def test_round_trip():
    """Test nothing is lost when lexing a typical log."""
    log = open(Path(__file__).parent / "thesis.log").read()
    for line in log.splitlines():
        assert line == "".join(token[1] for token in lex(line))


# TODO: I'm guessing I intended to write tests for these

# Underfull vbox warning followed by page numbers and noise
EDGE_CASE_1 = r"""Underfull \vbox (badness 4378) has occurred while \output is active [7]
 [8] [9 <./chapters/fiducial_marker_system//img/bad_marker_closeup.jpg> <./chapters/
 fiducial_marker_system//img/histogram_matching_graph.png>] [10 <./chapters/fiducial_
 marker_system//img/histogram_matching_image.png (PNG copy)> <./chapters/fiducial_marker
 _system//img/parameters_of_interest_distance.png> <./chapters/fiducial_marker_system//
 img/parameters_of_interest_size.png>] [11 <./chapters/fiducial_marker_system//img/
 sinusoid_marker5_frame000.png (PNG copy)> <./chapters/fiducial_marker_system//img/
 sinusoid_marker6_frame000.png (PNG copy)> <./chapters/fiducial_marker_system//img/
 sinusoid_marker5_frame000_cropped.png (PNG copy)> <./chapters/fiducial_marker_system//
 img/sinusoid_marker6_frame000_cropped.png (PNG copy)> <./chapters/fiducial_marker_
 system//img/sinusoid_marker5_stds.png> <./chapters/fiducial_marker_system//img/sinusoid
 _marker6_stds.png>] [12 <./chapters/fiducial_marker_system//img/sinusoid_marker5_
 stdtrend.png> <./chapters/fiducial_marker_system//img/sinusoid_marker6_stdtrend.png>])
 (./chapters/checkerboards/checkerboards.tex [13] [14 <./chapters/fiducial_marker_system
 //img/marker_parameter_histogram_first.png>] [15 <./chapters/fiducial_marker_system//
 img/marker_parameter_histogram_second.png>] [16]""".replace(
    "\n", ""
)

# Output from package inside noise
EDGE_CASE_2 = """) (/usr/local/texlive/2019/texmf-dist/tex/latex/fnpct/fnpct.sty (/usr/
local/texlive/2019/texmf-dist/tex/latex/koma-script/scrlfile.sty) (/usr/local/texlive/
2019/texmf-dist/tex/latex/filehook/filehook-scrlfile.sty) (/usr/local/texlive/2019/
texmf-dist/tex/latex/translations/translations.sty)) (/usr/local/texlive/2019/texmf-dist
/tex/latex/footmisc/footmisc.sty) (/usr/local/texlive/2019/texmf-dist/tex/latex/fnbreak
/fnbreak.sty) (/usr/local/texlive/2019/texmf-dist/tex/latex/todonotes/todonotes.sty
(/usr/local/texlive/2019/texmf-dist/tex/latex/pgf/frontendlayer/tikz.sty (/usr/local/
texlive/2019/texmf-dist/tex/latex/pgf/utilities/pgffor.sty (/usr/local/texlive/2019/
texmf-dist/tex/latex/pgf/utilities/pgfkeys.sty (/usr/local/texlive/2019/texmf-dist/tex/
generic/pgf/utilities/pgfkeys.code.tex)) (/usr/local/texlive/2019/texmf-dist/tex/latex/
pgf/math/pgfmath.sty (/usr/local/texlive/2019/texmf-dist/tex/generic/pgf/math/pgfmath.
code.tex)) (/usr/local/texlive/2019/texmf-dist/tex/generic/pgf/utilities/pgffor.code.tex
(/usr/local/texlive/2019/texmf-dist/tex/generic/pgf/math/pgfmath.code.tex))) (/usr/
local/texlive/2019/texmf-dist/tex/generic/pgf/frontendlayer/tikz/tikz.code.tex (/usr/
local/texlive/2019/texmf-dist/tex/generic/pgf/libraries/pgflibraryplothandlers.code.tex)
(/usr/local/texlive/2019/texmf-dist/tex/generic/pgf/modules/pgfmodulematrix.code.tex)
(/usr/local/texlive/2019/texmf-dist/tex/generic/pgf/frontendlayer/tikz/libraries/
tikzlibrarytopaths.code.tex))) (/usr/local/texlive/2019/texmf-dist/tex/generic/pgf/
frontendlayer/tikz/libraries/tikzlibrarypositioning.code.tex) (/usr/local/texlive/2019/
texmf-dist/tex/generic/pgf/frontendlayer/tikz/libraries/tikzlibraryshadows.code.tex
(/usr/local/texlive/2019/texmf-dist/tex/generic/pgf/frontendlayer/tikz/libraries/
tikzlibraryfadings.code.tex (/usr/local/texlive/2019/texmf-dist/tex/generic/pgf/
libraries/pgflibraryfadings.code.tex)))) (/usr/local/texlive/2019/texmf-dist/tex/latex/
cleveref/cleveref.sty) (/usr/local/texlive/2019/texmf-dist/tex/latex/subfiles/subfiles.
sty (/usr/local/texlive/2019/texmf-dist/tex/latex/tools/verbatim.sty))) (./mph/maths.
tex) (./commands.tex) (./acronyms.tex) (./symbols.tex) (/usr/local/texlive/2019/
texmf-dist/tex/latex/pythontex/pythontex.sty (/usr/local/texlive/2019/texmf-dist/tex/
latex/fvextra/fvextra.sty
(/usr/local/texlive/2019/texmf-dist/tex/latex/fancyvrb/fancyvrb.sty
Style option: `fancyvrb' v3.2a <2019/01/15> (tvz))
(/usr/local/texlive/2019/texmf-dist/tex/latex/upquote/upquote.sty) (/usr/local/texlive/
2019/texmf-dist/tex/latex/lineno/lineno.sty)) (/usr/local/texlive/2019/texmf-dist/tex/
generic/xstring/xstring.sty (/usr/local/texlive/2019/texmf-dist/tex/generic/xstring/
xstring.tex)) (/usr/local/texlive/2019/texmf-dist/tex/latex/pgfopts/pgfopts.sty) (/usr/
local/texlive/2019/texmf-dist/tex/latex/caption/newfloat.sty)) (/usr/local/texlive/
texmf-local/tex/latex/pythontexfigures/pythontexfigures.sty) (./Thesis.aux) (/usr/local/
texlive/2019/texmf-dist/tex/latex/base/ts1cmr.fd) (/usr/local/texlive/2019/texmf-dist/
tex/latex/lm/t1lmr.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/microtype/mt-cmr.
cfg)""".replace(
    "\n", ""
)

# Package warning with continuation, followed by message on its own line
EDGE_CASE_3 = """Package caption Warning: Unsupported document class (or package) detected,
(caption)                usage of the caption package is not recommended.
See the caption package documentation for explanation.

"""

# File with space in name
EDGE_CASE_4 = """(./include file.tex) [1{/usr/local/texlive/2019/texmf-var/fonts/map/
pdftex/updmap/pdftex.map}] (./test.aux) )</usr/local/texlive/2019/texmf-dist/fonts/
type1/public/amsfonts/cm/cmr10.pfb>""".replace(
    "\n", ""
)
