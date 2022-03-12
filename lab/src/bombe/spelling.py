import collections
import csv
from itertools import repeat
from pathlib import Path
from typing import Union

from techiaith.utils.bitext import Sentence

import hunspell
import pandas as pd
import sacremoses


class SpellCheck:
    """Encapsulate spell checking and misspelling of sentences and words."""

    def __init__(self,
                 lang: str,
                 dict_path: Union[Path, str],
                 spelling_dir: Path):
        self.lang = lang
        self.dict_path = dict_path
        self.speller = self._make_speller()
        self.misspelt_words = collections.Counter()
        self.misspelt_sentences = collections.defaultdict(set)
        self.spelling_dir = spelling_dir
        self.tokenizer = sacremoses.MosesTokenizer()

    # Pickle protocol interface - allow use with multiprocessing.
    # Hunspell instances cannot be pickled.

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['speller']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        speller = self._make_speller()
        self.speller = speller

    def _path_for_topic(self, topic):
        return Path(self.spelling_dir, f'{self.lang}_{topic}.csv')

    def _append_to_csv(self, data, topic, source_path):
        # invariant :- data should always contain the key 'words'
        columns = tuple(data.keys()) + ('source_path',)
        data['source_path'] = list(repeat(source_path, len(data['words'])))
        df = pd.DataFrame(data, columns=columns)
        path = self._path_for_topic(topic)
        header = not path.exists()
        mode = 'a' if path.exists() else 'w'
        df.to_csv(path,
                  mode=mode,
                  header=header,
                  columns=columns,
                  quoting=csv.QUOTE_NONNUMERIC)

    def _save_misspelt_words(self, source_path):
        data = dict(words=self.misspelt_words.keys(),
                    count=self.misspelt_words.values())
        self._append_to_csv(data, 'words', source_path)

    def _save_misspelt_sentences(self, source_path: Path):
        norm_data = dict((tid, ', '.join(filter(None, map(str, words))))
                         for (tid, words) in self.misspelt_sentences.items()
                         if len(words))
        data = dict(translation_id=norm_data.keys(),
                    words=norm_data.values())
        self._append_to_csv(data, 'sentences', source_path)

    def _make_speller(self):
        return hunspell.Hunspell(f'{self.lang}_GB',
                                 hunspell_data_dir=self.dict_path)

    def track_misspellings(self,
                           translation_id: int,
                           sentence: Sentence,
                           source_path: Path) -> bool:
        """Track mispellings in each sentence of the given `sentences`.

        Return True iif any mispellings where detected.
        """
        misspelt_words = (token
                          for token in self.tokenizer.tokenize(sentence.text)
                          if token.isalpha() and not self.speller.spell(token))
        for word in misspelt_words:
            self.misspelt_words[word] += 1
            self.misspelt_sentences[translation_id].add(word)

    def misspelt(self, translation_id: int) -> bool:
        return bool(self.misspelt_sentences.get(translation_id))

    def save(self, source_path: Path):
        self._save_misspelt_words(source_path)
        self._save_misspelt_sentences(source_path)
