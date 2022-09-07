#!/usr/bin/bash

DICT_DIR=$1
CY_HUNSPELL_GIT_REPO="github.com/techiaith/hunspell-cy"
HUNSPELL_EN_DICT_URL="https://raw.githubusercontent.com/ropensci/hunspell/master/inst/dict"


if [ ! -d docker-hunspell-cy ]; then
    git clone https://${CY_HUNSPELL_GIT_REPO}
fi
git pull
cp hunspell-cy/cy_GB.{aff,dic} ${DICT_DIR}/.
for suffix in dic aff
do
    curl -o ${DICT_DIR}/en_GB.${suffix} ${HUNSPELL_EN_DICT_URL}/en_GB.${suffix}
done

