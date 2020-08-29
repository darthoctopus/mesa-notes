#!/bin/bash
excise() {
        FILE=$1
        FIRST=$2
        LAST=$3
        OUT=$4

        pdfseparate -f $FIRST -l $LAST $FILE "scratch/out-%02d.pdf"
        pdfunite scratch/out-*.pdf scratch/$OUT
        rm -rf scratch/out-*.pdf
}

excise MESA_notes.pdf 1 5 MESA_1.pdf
excise MESA_notes.pdf 6 11 MESA_2.pdf
excise MESA_notes.pdf 12 22 MESA_3.pdf
excise MESA_notes.pdf 23 29 MESA_4.pdf
excise MESA_notes.pdf 30 33 MESA_5.pdf
excise MESA_notes.pdf 34 37 MESA_appendix.pdf
