from collections import defaultdict
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import Dict, Tuple
import os


open_utf8 = partial(open, encoding='utf-8')


ExperimentPath = partial(Path, '/experiments')


class DirectoryTree:
    """Iterator for directory trees."""

    def __init__(self, path):
        self.path = Path(path)

    def __iter__(self):
        for (top, _, filenames) in os.walk(self.path):
            for filename in filenames:
                yield Path(top, filename)


def segment_stats(work_dir: Path, langs: Tuple):
    """Calculate segment statistics.

    Corpora located in `work_dir` for the given `langs` are used to
    calcualte number of words and sentences.
    """
    stats = defaultdict(dict)
    for filename in os.listdir(work_dir):
        if filename.endswith(langs):
            with open(Path(work_dir, filename)) as fp:
                lines = fp.readlines()
                segs = (line.split(' ') for line in lines)
                stats['n_sentences'] = len(lines)
                stats['n_words'] = sum(map(len, segs))
    return stats


def ensure_folders_exist(*paths):
    """Ensure any and all paths exist on disk."""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def file_sizes(dirname: Path) -> Dict[str, Dict]:
    """Calculate file sizes in a directory tree rooted at `dirname`.

    Returns a nested of map of stat-category -> {path: value}.
    """
    stat_key = str(dirname)
    stats = {stat_key: defaultdict(dict)}
    path_sizes = defaultdict(dict)
    for path in DirectoryTree(dirname):
        stat = path.stat()
        size = Decimal(stat.st_size / pow(1000, 2))
        path_sizes[path.name] = size
    total = Decimal(sum(path_sizes.values()))
    stats[stat_key]['total_mb'] = '{:0.3}'.format(total)
    stats[stat_key]['sizes_mb'] = dict((k, '{:0.3}'.format(v))
                                       for (k, v) in path_sizes.items())
    return stats


def readlines(path: Path):
    with open_utf8(path) as fp:
        lines = fp.readlines()
    return list(line.strip('\n').strip() for line in lines)
