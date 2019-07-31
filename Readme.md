# QuieTeX

Minimal command-line tool which filters and colours the output of `pdflatex` in real-time.
Not a build tool, doesn't do any clever summaries, just makes it easier to watch.

To install:
```bash
pip3 install -e .
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
