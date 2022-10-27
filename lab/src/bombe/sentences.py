from collections import namedtuple
from functools import partial
from itertools import filterfalse
from pathlib import Path
from typing import Callable, Dict, Generator, Sequence, Tuple, Union
import csv

import pandas as pd
from techiaith.utils.bitext import LanguagePair, Sentence, to_bitext

from .spelling import SpellCheck
from .utils import fs


CLEANED_SUFFIX = '.cleaned.csv'


Translation = namedtuple('Translation',
                         ('id',
                          'classifier',
                          'source',
                          'target',
                          'langs'))


def translation(*args):
    source_path = args[-1]
    uniq_args = args[:-1]
    idx = hash(uniq_args)
    targs = (idx,) + uniq_args + (source_path,)
    return Translation(*targs)


def is_suspicious_content(langs: LanguagePair,
                          sentence_pair: Sentence) -> bool:
    for sent in sentence_pair:
        if sent.text.strip() in langs:
            return True
    return False


def clean_translations(
        source_path: Path,
        langs: Union[LanguagePair, Tuple],
        spell_checkers: Dict[str, SpellCheck]
) -> Generator[Translation, None, None]:
    label = source_path.parent.parts[-1]
    bitext_seq = to_bitext(source_path, langs)
    filter_fn = partial(is_suspicious_content, langs)
    filtered = filterfalse(filter_fn, bitext_seq)
    for sents in filtered:
        (source, target) = sents
        sents_by_lang = {source.lang: source, target.lang: target}
        tr = translation(label,
                         source.text,
                         target.text,
                         f'{source.lang}-{target.lang}')
        for lang in langs:
            sent = sents_by_lang[lang]
            spell_checker = spell_checkers[lang]
            spell_checker.track_misspellings(tr.id, sent, source_path)
            if spell_checker.misspelt(tr.id):
                break
        else:
            yield tr


def _to_csv(translations, columns, export_path):
    df = pd.DataFrame(translations, columns=columns)
    df.drop_duplicates(inplace=True)
    df.to_csv(export_path,
              columns=columns,
              index=False,
              quoting=csv.QUOTE_NONNUMERIC)


def clean(langs: LanguagePair,
          spell_checkers: Dict[str, SpellCheck],
          columns: Tuple,
          export_dir: Path,
          source_path: Path):
    export_filename = source_path.name.split('.')[0] + CLEANED_SUFFIX
    export_path = export_dir / export_filename
    translations = clean_translations(source_path,
                                      langs,
                                      spell_checkers)
    _to_csv(translations, columns, export_path)
    for lang in langs:
        spell_checkers[lang].save(source_path)


def load(export_dir: Path,
         columns: Sequence[str]) -> pd.DataFrame:
    """Load a data frame from a CSV file.

    Any column in `drop_columns` will be attempted to be removed
    from the data frame before resetting the index and returning it.
    """
    dfs = []
    df = pd.DataFrame(columns=columns)
    for export_path in fs.DirectoryTree(export_dir):
        if export_path.name.endswith(CLEANED_SUFFIX):
            dfs.append(pd.read_csv(export_path, index_col='id'))
    df = pd.concat(dfs)
    df.drop_duplicates(('source', 'target', 'classifier', 'langs'),
                       inplace=True)
    return df
