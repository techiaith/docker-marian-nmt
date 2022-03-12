from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import datetime
import hashlib
import pickle
import re
import uuid

from techiaith.utils.bitext import LanguagePair

from .utils import fs


TIMESTAMP_PATTERN = ('^\\[(?P<log_date>\d{4}\-\d{2}\-\d{2})\s+'
                     '(?P<log_time>\d{2}:\d{2}:\d{2})\\]\s+')

timestamp_regexp = re.compile(TIMESTAMP_PATTERN)


def wall_time_from_log(log):
    (strdate, strtime) = (log['log_date'], log['log_time'])
    wall_time = get_wall_time(strdate, strtime)
    return wall_time


def _find_start_time(fp):
    line = fp.readline()
    log = timestamp_regexp.search(line)
    if log is not None:
        return datetime.datetime.fromtimestamp(wall_time_from_log(log))


def _find_end_time(fp):
    endpos = fp.seek(0, 2)
    fp.seek(endpos - 1024)
    found_fin = False
    while not found_fin:
        line = fp.readline()
        found_fin = 'finished' in line
        if not line:
            break
    log = timestamp_regexp.search(line)
    if log is not None:
        return datetime.datetime.fromtimestamp(wall_time_from_log(log))


def duration(log_path):
    """Return training duration in hours."""
    with open(log_path) as fp:
        start = _find_start_time(fp)
        end = _find_end_time(fp)
    if all([start, end]):
        return (end - start).seconds / 60 / 60
    return -1


def get_wall_time(date_str, time_str, tformat='%Y-%m-%d %H:%M:%S'):
    t = datetime.datetime.strptime(date_str + ' ' + time_str, tformat)
    return t.timestamp()


class Session:

    _obj = None

    folder: Path = Path('/experiments')

    filename: str = 'bombe-sessions.pickle'

    current_session_marker: str = 'current'

    _langs = None

    def __init__(self, langs, ident, comment=''):
        self.langs = langs
        self.ident = ident
        self.comment = comment
        self.created = datetime.datetime.utcnow()
        self.settings = {}
        self.results = {}
        self._train_progress = 0

    def __str__(self):
        lang_dir = '-'.join(self.langs)
        return f'{lang_dir}_{self.ident}'

    def _parse_langs(self, langs: Union[str, Tuple, LanguagePair]):
        if isinstance(langs, str):
            (src_lang, _, tgt_lang) = re.split(r'(-|_)', langs)
            langs = (src_lang, tgt_lang)
        return langs

    @property
    def langs(self):
        return self._langs

    @langs.setter
    def langs(self, lngs: Union[str, Tuple, LanguagePair]):
        self._langs = LanguagePair(*self._parse_langs(lngs))

    @property
    def folders(self) -> Dict:
        folders = {}
        for (k, v) in list(self.settings.items()):
            if isinstance(v, str) and v.startswith(str(self.folder)):
                v = Path(v.format(self) if '{}' in v else v)
            elif isinstance(v, Path):
                pass
            else:
                continue
            folders[k] = v
        return folders

    @classmethod
    def path(cls):
        return Path(cls.folder, cls.filename)

    @classmethod
    def registry(cls):
        return cls._load()

    @classmethod
    def new(cls,
            langs: Union[Tuple, str],
            comment: Optional[str] = None,
            **settings) -> object:
        uniq = hashlib.md5(uuid.uuid4().bytes).hexdigest()
        obj = cls(langs, uniq[-8:], comment=comment)
        cls.save(obj, **settings)
        return obj

    @classmethod
    def is_active(cls):
        return cls.path().is_file()

    @classmethod
    def get(cls, use_cache=True):
        if cls._obj is None or not use_cache:
            return cls._load(cls.current_session_marker)
        return cls._obj

    @classmethod
    def _load(cls, tsid: str = None) -> Union[object, dict]:
        path = cls.path()
        if path.exists():
            with open(cls.path(), 'rb') as fp:
                sessions = pickle.load(fp)
            if tsid is not None:
                return sessions.get(tsid)
            return sessions

    @classmethod
    def load(cls, tsid):
        cls._obj = cls._load(tsid)
        return cls._obj

    def get_results(self, tsid=None, summarize=True):
        ts = self.load(tsid) if tsid else self
        data = ts.results
        if summarize:
            for (split_k, result) in list(data.items()):
                for k in result:
                    if k == 'stats':
                        for dirname in list(data[k]):
                            for path in list(data[k][dirname]):
                                del data[k][dirname][path]['sizes_mb']
        return data

    def end(self):
        sessions = self._load()
        had_current = bool(sessions.pop(self.current_session_marker, None))
        if had_current:
            self._save(sessions)

    def _save(self, sessions: dict):
        with open(self.path(), 'wb') as fp:
            pickle.dump(sessions, fp)

    def save(self):
        """Set the training session id."""
        path = self.path()
        sessions = {}
        if path.is_file():
            with open(self.path(), 'rb') as fp:
                sessions.update(pickle.load(fp))
        for k in (self.current_session_marker, str(self)):
            sessions[k] = self
        self.ensure_folders_exist()
        self._save(sessions)

    def get_progress(self):
        return self._train_progress

    def save_progress(self, val):
        self._train_progress = val
        self.save()

    def ensure_folders_exist(self):
        for (name, path) in list(self.folders.items()):
            fs.ensure_folders_exist(path)
            self.settings[name] = path

    def kfold_split_path(self, topic: str, k: int, *leafs) -> Path:
        path = Path(self.folders[f'{topic}_dir'],
                    f'split_{k}',
                    *leafs)
        if leafs:
            folder = path.parent
        else:
            folder = path
        fs.ensure_folders_exist(folder)
        return path
