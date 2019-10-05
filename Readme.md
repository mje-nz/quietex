# QuieTeX
[![PyPI Package latest release](https://img.shields.io/pypi/v/quietex.svg)](https://pypi.org/project/quietex)
[![Supported versions](https://img.shields.io/pypi/pyversions/quietex.svg)](https://pypi.org/project/quietex)

Minimal command-line tool which filters and colours the output of `pdflatex` in real-time.
Not a build tool, doesn't do any clever summaries, just makes it easier to watch.



## Features
* Hides open/close file logging
* Colours errors red
* Colours warnings yellow
* TeX input prompt works in `errorstopmode` and `scrollmode`
* `latexmk` integration



## Usage
To install:
```bash
pip3 install quietex
```

To use:
```bash
quietex pdflatex test.tex
```

To use with `latexmk`, add this to your `latexmkrc`:
```perl
# Make output prettier
eval `quietex --latexmkrc`;
```



## Development
To install in editable mode:
```bash
pip3 install -e .
```

Use [pre-commit](https://pre-commit.com) to check and format changes before committing:
```bash
pip install pre-commit
pre-commit install
```



## Misc
TODO:
* Add tests
* Add example before/after to readme
* Show open-files stack before warnings and errors
* Display page numbers in real-time, before the end of the line
* Completions for TeX prompt
* Syntax highlighting for TeX snippets
* Configurable styles
* Verbose mode, note about dim on macOS

The approach for colouring `latexmk` messages is inspired by [this Stack Overflow answer](https://tex.stackexchange.com/a/406370).
The way I've packaged `latexmkrc` is taken straight from [mje-nz/pythontexfigures](https://github.com/mje-nz/pythontexfigure), my library for generating good-looking figures by integrating Python scripts into LaTeX documents.
