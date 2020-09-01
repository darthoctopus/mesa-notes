#!/bin/bash

all: parts

MESA_notes.pdf:
	pandoc -f markdown+tex_math_single_backslash-latex_macros -s -o "MESA_notes.tex" "MESA_notes.md" --number-sections --natbib --highlight-style=breezedark && latexmk "MESA_notes.tex" -interaction=nonstopmode -shell-escape -synctex=1 -xelatex -bibtex-cond -quiet -silent -f

parts: MESA_notes.pdf
	Scripts/excise.sh MESA_notes.pdf 1 5 MESA_1.pdf
	Scripts/excise.sh MESA_notes.pdf 6 11 MESA_2.pdf
	Scripts/excise.sh MESA_notes.pdf 12 22 MESA_3.pdf
	Scripts/excise.sh MESA_notes.pdf 23 29 MESA_4.pdf
	Scripts/excise.sh MESA_notes.pdf 30 35 MESA_5.pdf
	Scripts/excise.sh MESA_notes.pdf 36 39 MESA_appendix.pdf

clean:
	rm MESA_notes.pdf
	rm scratch/*.pdf
