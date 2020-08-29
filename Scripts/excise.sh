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

excise $1 $2 $3 $4
