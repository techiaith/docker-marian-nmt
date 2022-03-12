#!/bin/bash

target_lang=$1
valid_target_corpus=$2
output_translation_file=$3
cat $output_translation_file \
    | python -m sacremoses -q -l $target_lang \
	     normalize --remove-control-chars \
	     detruecase \
	     detokenize \
    | python -m sacrebleu -t wm17 -l $target_lang $valid_target_corpus

