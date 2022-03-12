#!/bin/bash

valid_log=$1

strings ${valid_log} \
    | cat \
    | grep bleu-detok \
    | sort -rg -k12,12 -t' ' \
    | cut -f8 -d' ' \
    | head -n1
