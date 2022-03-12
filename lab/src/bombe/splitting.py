from collections import defaultdict, namedtuple
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import csv
import os

from techiaith.utils.bitext import LanguagePair
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd


GroupLabels = namedtuple('GroupLabels', ('classified', 'unclassified'))

_tset_labels = ('train', 'valid', 'test')

TrainingSets = namedtuple('TrainingSets', _tset_labels)

sets = TrainingSets(*_tset_labels)


def _to_csv(dataset: Union[pd.DataFrame, pd.Series],
            path: Union[str, Path],
            **kw) -> None:
    dataset.to_csv(path,
                   header=kw.pop('header', 0),
                   index=kw.pop('index', False),
                   quoting=kw.pop('quoting', csv.QUOTE_NONNUMERIC),
                   **kw)


def _ensure_unique(test_set, train_set):
    df = pd.merge(test_set,
                  train_set,
                  on=['source', 'target'],
                  how='left',
                  indicator='Exist')
    df['Exist'] = np.where(df.Exist == 'both', True, False)
    df = df.loc[df['Exist'] == True]  # noqa: E712
    df = df.drop(['Exist', 'classifier_y', 'langs_y'], axis=1)
    df = df.rename(columns={'classifier_x': 'classifier',
                            'langs_x': 'langs'})
    test_set = pd.merge(test_set,
                        df,
                        on=['source', 'target'],
                        how='outer',
                        indicator=True)
    test_set = test_set.query('_merge != "both"')
    test_set = test_set.drop('_merge', axis=1)
    test_set = test_set.reset_index(drop=True)
    test_set = test_set.drop(['classifier_y', 'langs_y'], axis=1)
    test_set = test_set.rename(columns={'classifier_x': 'classifier',
                                        'langs_x': 'langs'})

    return test_set


def classified_split(langs: Union[LanguagePair, Tuple],
                     corpus: pd.DataFrame,
                     classifier_group: pd.Series,
                     group_labels: GroupLabels,
                     random_state: Optional[int] = 42,
                     shuffle: Optional[bool] = True,
                     test_size: Optional[float] = 0.1):
    grouped = corpus.groupby(classifier_group)
    classified = grouped.get_group(group_labels.classified)
    unclassified = grouped.get_group(group_labels.unclassified)
    (train_set, test_set) = train_test_split(classified,
                                             random_state=random_state,
                                             shuffle=shuffle,
                                             test_size=test_size)
    train_set = pd.concat([train_set, unclassified])
    test_set = _ensure_unique(test_set, train_set)
    return tuple(df.dropna(how='any') for df in (train_set, test_set))


def kfold_cv_split(langs: LanguagePair,
                   corpus: pd.DataFrame,
                   classifier_group: pd.Series,
                   group_labels: GroupLabels,
                   k: int,
                   test_size: float) -> Dict[str, pd.DataFrame]:
    splits = defaultdict(list)
    # folds = np.array_split(corpus.sample(frac=1), 10)
    for _ in range(k):
        df = corpus.sample(frac=1)
        (train_set, valid_set) = classified_split(langs,
                                                  df,
                                                  classifier_group,
                                                  group_labels,
                                                  test_size=test_size)
        splits['train'].append(train_set)
        splits['valid'].append(valid_set)
    return splits


def split(langs: LanguagePair,
          corpus: pd.DataFrame,
          classifier_group: pd.Series,
          group_labels: GroupLabels,
          test_size: int = 0.1,
          k_folds: int = 10) -> Tuple[List[str], str]:
    (train_set, test_set) = classified_split(langs,
                                             corpus,
                                             classifier_group,
                                             group_labels,
                                             test_size=test_size)
    train_sets = kfold_cv_split(langs,
                                train_set,
                                classifier_group,
                                group_labels,
                                k_folds,
                                test_size)
    return (train_sets, test_set)


def save(train_sets: Dict[str, pd.DataFrame],
         test_set: pd.DataFrame,
         langs: Union[LanguagePair, Tuple],
         storage_path: Path,
         col_names: Optional[Tuple] = ('source', 'target'),
         filename_pattern: str = 'corpus.split_{split_n:02d}.{label}.{lang}'
         ) -> Tuple[Path]:
    """Store train/test split data to unqiue paths based in `work_dir`.

    Return a tuple of the paths where the data is saved to.
    """
    storage_path.mkdir(parents=True, exist_ok=True)
    paths = []
    for (lang, col_name) in zip(langs, col_names):
        path = Path(storage_path, f'corpus.test.{lang}')
        df = test_set[col_name]
        _to_csv(df, path, columns=(col_name,))
        paths.append(path)
    labels = tuple(train_sets)
    for label in labels:
        splits = train_sets[label]
        for (split_n, split) in enumerate(splits, start=1):
            for (col_name, lang) in zip(col_names, langs):
                filename = filename_pattern.format(split_n=split_n,
                                                   label=label,
                                                   lang=lang)
                sents = split[col_name]
                path = Path(storage_path, filename)
                _to_csv(sents, path, columns=(col_name,))
                paths.append(path)
    return paths


def paths(work_dir: Path,
          langs: LanguagePair,
          label: str) -> List[Path]:

    def sort_key(path):
        parts = path.name.rsplit('.')
        (spl1t, _, lang) = parts[1:]
        return (spl1t, langs.index(lang))

    paths = sorted((Path(work_dir, filename)
                    for filename in os.listdir(work_dir)
                    if all([filename.startswith('corpus'),
                            label in filename,
                            filename.endswith(langs)])),
                   key=sort_key)
    it = iter(paths)
    return list(zip(it, it))
