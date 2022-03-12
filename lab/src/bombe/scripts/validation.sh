#!/bin/bash
target_lang=$1
valid_target_corpus=$2
cat $3 \
    | sed 's/\@\@ //g' \
    | ${MARIANPATH}/scripts/moses-scripts/scripts/recaser/detruecase.perl 2>dev/null \
    | ${MARIANPATH}/scripts/moses-scripts/scripts/tokenizer/detokenizer.perl -l $target_lang 2> /dev/null \
    | ${MARIANPATH}/scripts/moses-scripts/scripts/generic/multi-bleu-detok.perl $valid_target_corpus \
    | sed -r 's/BLEU = ([0-9.]+),.*/\1/'
