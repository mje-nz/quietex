# QuieTeX
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
