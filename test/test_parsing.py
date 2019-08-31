"""Tests for parsing module."""

from pathlib import Path

from quietex.parsing import LatexLogParser
from quietex.tokens import *  # noqa: F403

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


def test_parse_other():
    """Test parsing some uninteresting log messages."""
    p = LatexLogParser()
    for msg in [
        "This is pdfTeX, Version 3.14159265-2.6-1.40.20 (TeX Live 2019) (preloaded format=pdflatex)",  # noqa: B950
        r" restricted \write18 enabled.",
        "LaTeX2e <2018-12-01>",
        "Document Class: article 2018/09/03 v1.4i Standard LaTeX document class",
        "Output written on test.pdf (1 page, 12659 bytes).",
        "Transcript written on test.log.",
    ]:
        assert p.parse_line(msg) == [OtherToken(msg)]


def test_parse_file_opening_simple():
    """Test parsing some simple file open messages."""
    p = LatexLogParser()
    for file in [
        "./test.tex",
        "/usr/local/texlive/2019/texmf-dist/tex/latex/base/article.cls",
    ]:
        assert p.parse_line("(" + file) == [OpenFileToken("(" + file, file)]


def test_parse_file_closing_simple():
    """Test parsing the simplest file close message."""
    p = LatexLogParser()
    assert p.parse_line(")") == [CloseFileToken()]


def test_parse_open_close_file():
    """Test parsing an open file message followed by a close file message."""
    p = LatexLogParser()
    assert p.parse_line("(./test.tex)") == [
        OpenFileToken("(./test.tex", "./test.tex"),
        CloseFileToken(),
    ]


def test_parse_files_complex():
    """Test parsing many open/close file messages on one line."""
    p = LatexLogParser()
    msg = ")) (/usr/a) (/usr/b (/usr/c (/usr/d)) (/usr/e) (/usr/f)) (/usr/g (/usr/h))"
    assert p.parse_line(msg) == [
        CloseFileToken(),
        CloseFileToken(),
        OpenFileToken(" (/usr/a", "/usr/a"),
        CloseFileToken(),
        OpenFileToken(" (/usr/b", "/usr/b"),
        OpenFileToken(" (/usr/c", "/usr/c"),
        OpenFileToken(" (/usr/d", "/usr/d"),
        CloseFileToken(),
        CloseFileToken(),
        OpenFileToken(" (/usr/e", "/usr/e"),
        CloseFileToken(),
        OpenFileToken(" (/usr/f", "/usr/f"),
        CloseFileToken(),
        CloseFileToken(),
        OpenFileToken(" (/usr/g", "/usr/g"),
        OpenFileToken(" (/usr/h", "/usr/h"),
        CloseFileToken(),
        CloseFileToken(),
    ]


def test_parse_message_inside_files():
    """Test parsing a message hidden amongst open/close file messages."""
    p = LatexLogParser()
    msg = [
        "(/usr/local/texlive/2019/texmf-dist/tex/latex/fp/fp.sty",
        " `Fixed Point Package', Version 0.8, April 2, 1995 (C) Michael Mehlich",
        " (/usr/local/texlive/2019/texmf-dist/tex/latex/fp/defpattern.sty)",
    ]
    assert p.parse_line("".join(msg)) == [
        OpenFileToken(msg[0], msg[0].strip("( ")),
        OtherToken(msg[1]),
        OpenFileToken(msg[2][:-1], msg[2].strip("( )")),
        CloseFileToken(),
    ]


def test_parse_message_followed_by_close():
    """Test parsing a message hidden amongst open/close file messages."""
    p = LatexLogParser()
    msg = [
        "(/usr/local/texlive/2019/texmf-dist/tex/latex/fp/fp.sty",
        " `Fixed Point Package', Version 0.8, April 2, 1995 (C) Michael Mehlich)",
        " (/usr/local/texlive/2019/texmf-dist/tex/latex/fp/defpattern.sty)",
    ]
    assert p.parse_line("".join(msg)) == [
        OpenFileToken(msg[0], msg[0].strip("( ")),
        OtherToken(msg[1][:-1]),
        CloseFileToken(),
        OpenFileToken(msg[2][:-1], msg[2].strip("( )")),
        CloseFileToken(),
    ]


def test_parse_message_inside_files_fancyvrb():
    """Test parsing the message from loading fancyvrb, which has brackets in it (!)."""
    p = LatexLogParser()
    msg = [
        "(/usr/local/texlive/2019/texmf-dist/tex/latex/fancyvrb/fancyvrb.sty",
        " Style option: `fancyvrb' v3.2a <2019/01/15> (tvz))",
        " (/usr/local/texlive/2019/texmf-dist/tex/latex/upquote/upquote.sty",
    ]
    assert p.parse_line("".join(msg)) == [
        OpenFileToken(msg[0], msg[0].strip("( ")),
        OtherToken(msg[1][:-1]),
        CloseFileToken(),
        OpenFileToken(msg[2], msg[2].strip(" (")),
    ]


def test_parse_message_inside_files_fancyvrb_minimal():
    """Test parsing the message from loading fancyvrb, which has brackets in it (!).

    Make sure it works without the next open message.
    """
    p = LatexLogParser()
    msg = [
        "(/usr/local/texlive/2019/texmf-dist/tex/latex/fancyvrb/fancyvrb.sty",
        " Style option: `fancyvrb' v3.2a <2019/01/15> (tvz))",
    ]
    assert p.parse_line("".join(msg)) == [
        OpenFileToken(msg[0], msg[0].strip("( ")),
        OtherToken(msg[1][:-1]),
        CloseFileToken(),
    ]


def test_parse_read_image():
    """Test parsing some read images messages"""
    p = LatexLogParser()
    # TODO: Names with spaces
    for msg in [
        "<./img/test.jpg>",
        " <./img/test.jpg>",
        "<./img/test.png>",
        "<./img/test.png (PNG copy)>",
        "</usr/local/texlive/2019/texmf-dist/fonts/type1/public/lm/lmbx10.pfb>",
    ]:
        assert p.parse_line(msg) == [ReadImageToken(msg)]


def test_parse_read_image_in_warning():
    """Test parsing a read image inside a page number at the end of a warning."""
    p = LatexLogParser()
    line = r"Underfull \vbox (badness 7963) has occurred while \output is active [2 <./test.png (PNG copy)>]"  # noqa: B950
    assert p.parse_line(line) == [
        WarningToken(
            r"Underfull \vbox (badness 7963) has occurred while \output is active"
        ),  # noqa: B950
        PageToken(" [2", "2"),
        ReadImageToken(" <./test.png (PNG copy)>"),
        OtherToken("]"),
    ]


def test_parse_read_aux():
    """Test parsing some read aux messages"""
    p = LatexLogParser()
    # TODO: Names with spaces
    for msg in [
        "{/usr/local/texlive/2019/texmf-dist/fonts/enc/dvips/lm/lm-mathit.enc}",
        "{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}",
    ]:
        assert p.parse_line(msg) == [ReadAuxToken(msg)]


def test_parse_read_aux_in_page():
    """Test parsing a read aux inside a page number."""
    p = LatexLogParser()
    line = "[1{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}]"
    assert p.parse_line(line) == [
        PageToken("[1", "1"),
        ReadAuxToken(
            "{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}"
        ),
        OtherToken("]"),
    ]


# New output from a simple test document with an error:
# ! Undefined control sequence.
# l.6 \badcommand


def test_parse_error():
    """Test parsing an error message."""
    p = LatexLogParser()
    msg = "! Undefined control sequence."
    assert p.parse_line(msg) == [ErrorToken(msg)]


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


def test_parse_simple_warnings():
    """Test parsing simple warning messages."""
    p = LatexLogParser()
    for msg in [
        r"Underfull \vbox (badness 10000) has occurred while \output is active",
        r"Overfull \hbox (2.79605pt too wide) detected at line 132",
        "LaTeX Warning: Marginpar on page 7 moved.",
        "Package natbib Warning: Citation `Siebert2009' on page 17 undefined on input line 22.",  # noqa: B950
        "pdfTeX warning (dest): name{Hfootnote.2} has been referenced but does not exist, replaced by a fixed one",  # noqa: B950
    ]:
        assert p.parse_line(msg) == [WarningToken(msg)]


# A few examples of page numbers and false positives from a complicated document
# [Loading MPS to PDF converter (version 2006.09.02).]
# ) (/usr/local/texlive/2019/texmf-dist/tex/latex/oberdiek/epstopdf-base.sty (/usr/local/texlive/2019/texmf-dist/tex/latex/oberdiek/grfext.sty) (/usr/local/texlive/2019/texmf-dist/tex/latex/latexconfig/epstopdf-sys.cfg)) (/usr/local/texlive/2019/texmf-dist/tex/latex/oberdiek/pdflscape.sty (/usr/local/texlive/2019/texmf-dist/tex/latex/graphics/lscape.sty)) ABD: EveryShipout initializing macros (/usr/local/texlive/2019/texmf-dist/tex/latex/translations/translations-basic-dictionary-english.trsl) (./pythontex-files-Thesis/Thesis.pytxmcr) (./pythontex-files-Thesis/Thesis.pytxpyg) (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/ot1lmr.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/omllmm.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/omslmsy.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/omxlmex.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/amsfonts/umsa.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/microtype/mt-msa.cfg) (/usr/local/texlive/2019/texmf-dist/tex/latex/amsfonts/umsb.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/microtype/mt-msb.cfg) (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/ot1lmss.fd) (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/ot1lmtt.fd) [1{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}] [2] (./Thesis.toc) (./Thesis.gls-abr [3] [4]) (./Thesis.sls [5] [6]) [7] [8] (./Thesis.tdo [9]) [10] (./chapters/fiducial_marker_system/fiducial_marker_system.tex  # noqa: B950
# [17 <./chapters/checkerboards//img/checkerboard.pdf>]
# [18]
#  [][][][]
# Underfull \vbox (badness 7963) has occurred while \output is active [2 <./chapters/fiducial_marker_system//img/basic_marker.png (PNG copy)>]  # noqa: B950
# Underfull \vbox (badness 10000) has occurred while \output is active [19]
# \OT1/lmr/bx/n/10.95 H \OT1/lmr/m/n/10.95 = [] [] \OML/lmm/m/it/10.95 :


def test_parse_page_number_simple():
    """Test parsing a simple page number."""
    p = LatexLogParser()
    assert p.parse_line("[1]") == [PageToken("[1]", "1")]


def test_parsing_page_number_complex():
    """Test parsing page numbers on the same line as other messages."""
    p = LatexLogParser()
    # TODO: [1{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}] [2] (./Thesis.toc)  # noqa: B950
    for msg in [
        "(./Thesis.gls-abr [1])",
        ") (/usr/local/texlive/2019/texmf-dist/tex/latex/lm/ot1lmtt.fd) [1]",
        "[1 <./chapters/fiducial_marker_system//img/basic_marker.png (PNG copy)>]",
        "[1{/usr/local/texlive/2019/texmf-var/fonts/map/pdftex/updmap/pdftex.map}]",
        r"Underfull \vbox (badness 10000) has occurred while \output is active [1]",
    ]:
        tokens = p.parse_line(msg)
        # Expliticly don't check text
        assert (PageToken, "1") in [(type(token), token.value) for token in tokens]


def test_parsing_page_number_complex_1():
    """Test parsing a page number inside an open/close file."""
    p = LatexLogParser()
    tokens = p.parse_line("(./Thesis.gls-abr [1])")
    assert tokens == [
        OpenFileToken("(./Thesis.gls-abr", "./Thesis.gls-abr"),
        PageToken(" [1]", "1"),
        CloseFileToken(),
    ]


def test_parsing_page_number_complex_2():
    """Test parsing a page number at the end of a warning."""
    p = LatexLogParser()
    msg = r"Underfull \vbox (badness 10000) has occurred while \output is active [1]"
    tokens = p.parse_line(msg)
    assert tokens == [WarningToken(msg[:-4]), PageToken(" [1]", "1")]


def test_parse_page_number_false_positives():
    """Test parsing things that look like page numbers but aren't."""
    p = LatexLogParser()
    for msg in ["[Loading MPS to PDF converter (version 2006.09.02).]", " [][][][]"]:
        assert p.parse_line(msg) == [OtherToken(msg)]


def test_round_trip():
    """Test nothing is lost when parsing a typical log."""
    p = LatexLogParser()
    log = open(Path(__file__).parent / "thesis.log").read()
    tokens = p.parse_text(log)
    assert log == "".join(token.text for token in tokens)


# Underfull vbox warning followed by page numbers and noise
edge_case_1 = r"""Underfull \vbox (badness 4378) has occurred while \output is active [7]
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
edge_case_2 = """) (/usr/local/texlive/2019/texmf-dist/tex/latex/fnpct/fnpct.sty (/usr/
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
edge_case_3 = """Package caption Warning: Unsupported document class (or package) detected,
(caption)                usage of the caption package is not recommended.
See the caption package documentation for explanation.

"""

# File with space in name
edge_case_4 = """(./include file.tex) [1{/usr/local/texlive/2019/texmf-var/fonts/map/
pdftex/updmap/pdftex.map}] (./test.aux) )</usr/local/texlive/2019/texmf-dist/fonts/
type1/public/amsfonts/cm/cmr10.pfb>""".replace(
    "\n", ""
)