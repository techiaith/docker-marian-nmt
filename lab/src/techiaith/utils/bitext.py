"""Utilities for working with pair of texts in two different languages."""
from collections import namedtuple
from functools import partial
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple, Union
import csv
import io
import logging
import os
import re
import unicodedata

from lxml import etree
from translate.storage import csvl10n, factory, tmx, wordfast
import pycld2 as cld2
import sacremoses as sm


log = logging.getLogger(__name__)


_wordfast_tags = re.compile('&t[A-Z];')


_replacements = (('\r\n', '\n'),
                 ('\n', ' '),
                 ('\t', ' ' * 4))

_repeated_chars = re.compile(r'(?P<char>[_\-\.]){2,}')


def _compile_non_lang_pattern(special_chars: str = ''):
    return re.compile(r"(?P<nlc>[^a-zA-Z0-9\s'\(\),-.:;!?%£$/"
                      f'{special_chars}])')


_non_lang_chars = {
    'cy': _compile_non_lang_pattern(r'ÁÂÄÉÊËÎÏÔÖÔÛŴŶáâäéêëîïôöôûŵŷ'),
    'en': _compile_non_lang_pattern()
}

LanguagePair = namedtuple('LanguagePair', ('source', 'target'))
"""A pair of languages used to describe a bitext."""


Sentence = namedtuple('Sentence', ('text', 'lang'))
"""A namedtuple storing a sentaece with given `text` in a language `lang`."""


SentenceSpec = namedtuple('SentenceSpec', ('lang', 'fieldname', 'text'))
"""A namedtuple storing the specification of a sentence (internal)."""


text_xpath = etree.XPath('text()')
"""Return text of xml node subtree."""


def remove_control_characters(s, unicat='C'):
    return ''.join(ch for ch in s if unicodedata.category(ch)[0] != unicat)


def normalize(text: str, lang: str = None) -> str:
    """Normalize `text` for a given `lang`."""
    for (char, replacement) in _replacements:
        text = text.replace(char, replacement)
    text = remove_control_characters(text)
    text = sm.MosesPunctNormalizer(lang=lang).normalize(text)
    regexp = _non_lang_chars.get(lang)
    if regexp:
        text = regexp.sub('', text)
    return text.strip()


def lang_detect(text: str) -> str:
    """Return 2-digit code of language detected in `text`.

    Return None if no reliable language could be detected.
    """
    try:
        (is_reliable, _, best_guesses) = cld2.detect(text, bestEffort=True)
        if not is_reliable:
            raise ValueError('No reliable language guessed from text', text)
    except Exception:
        return None
    lang_code = best_guesses[0][1]
    return lang_code


def _sort_by_language(langs: LanguagePair,
                      sent_spec: SentenceSpec) -> int:
    return langs.index(sent_spec.lang)


def sentences_from_lang_data(
        data: List[SentenceSpec],
        langs: Union[LanguagePair, tuple],
        fieldnames: Optional[Tuple[str, str]] = ('source', 'target')
) -> [Tuple[Sentence]]:
    """Return a 2-tuple of sentences from `data`.

    Sentences are returned in in the order described by `langs`.
    """
    sentences = []
    langs = LanguagePair(*langs)
    if any(ss.lang not in langs for ss in data):
        return tuple()
    sort_key = partial(_sort_by_language, langs)
    for sent_spec in sorted(data, key=sort_key):
        text = sent_spec.text
        if text is not None:
            text = normalize(text, sent_spec.lang)
            if _repeated_chars.match(text) is None:
                sentences.append(Sentence(text, sent_spec.lang))
    keep = len(sentences) == len(langs)
    keep &= all(lang_detect(sent.text) == sent.lang for sent in sentences)
    if keep:
        return tuple(sentences)
    return tuple()


class tmxunitl2(tmx.tmxunit):
    """Version of tmxunit with support for LeveL 2 of the TMX specification."""

    def getNodeText(self, lang_node, xml_space='preserve'):
        xml_text = super().getNodeText(lang_node, xml_space)
        if xml_text is not None and any(('{' in xml_text, '}' in xml_text)):
            terms = lang_node.iterdescendants(self.namespaced(self.textNode))
            node = next(terms, None)
            if node is not None:
                sep = ' ' if '{j' in xml_text else ''
                return sep.join(text_xpath(node))
            return None
        return xml_text


class tmxfilel2(tmx.tmxfile):
    """Version of tmxfile with support for Level 2 of the TMX specification."""
    UnitClass = tmxunitl2


def sentences_from_tmx_unit(
        unit: tmx.tmxunit,
        langs: Union[LanguagePair, tuple],
        fieldnames: Tuple,
        **kw) -> Tuple[Sentence]:
    """Return a 2-tuple of sentences from a `unit` in TMX file."""
    ss = []
    for fieldname in fieldnames:
        dom = getattr(unit, f'{fieldname}_dom', None)
        if dom is None:
            return None
        lang_val = next(iter(dom.attrib.values()))
        lang_val = lang_val.split('-')[0]  # e.g: cope with en-GB
        lang = lang_val.lower()  # guard against case-mismatch
        text = getattr(unit, fieldname)
        ss.append(SentenceSpec(lang, fieldname, text))
    return sentences_from_lang_data(ss, langs)


def sentences_from_csv_unit(
        unit: csvl10n.csvunit,
        langs: Union[LanguagePair, tuple],
        fieldnames: Tuple) -> Tuple[Sentence]:
    ss = []
    data = unit.todict()
    for (fieldname, lang) in zip(fieldnames, langs):
        text = data[fieldname]
        ss.append(SentenceSpec(lang, fieldname, text))
    return sentences_from_lang_data(ss, langs, fieldnames=fieldnames)


def sentences_from_wordfast_unit(
        unit: wordfast.WordfastUnit,
        langs: Union[LanguagePair, tuple],
        fieldnames: Tuple) -> Tuple[Sentence]:
    data = unit.dict
    wf_langs = tuple(lang.split('-')[0].lower()
                     for lang in (data['src-lang'], data['target-lang'])
                     if lang is not None)
    if not wf_langs or len(wf_langs) != 2:
        return None
    (src_lang, trg_lang) = wf_langs
    ss = []
    for (lang, fieldname) in zip(wf_langs, fieldnames):
        text = data[fieldname]
        match = _wordfast_tags.search(text)
        if match is not None:
            text = _wordfast_tags.sub('', text)
        ss.append(SentenceSpec(lang, fieldname, text))
    return sentences_from_lang_data(ss, langs)


class TSVDialect(csvl10n.DefaultDialect):
    delimiter = '\t'


csv.register_dialect('TAB', TSVDialect)


class tsvfile(csvl10n.csvfile):

    Extensions = ('tsv',)

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.dialect = 'TAB'

    def parse(self, csvsrc, **kw):
        text, encoding = self.detect_encoding(
            csvsrc, default_encodings=['utf-8', 'utf-16']
        )
        self.encoding = encoding or 'utf-8'
        inputfile = io.StringIO(text)
        try:
            fieldnames = csvl10n.detect_header(inputfile,
                                               self.dialect,
                                               self.fieldnames)
            self.fieldnames = fieldnames
        except csv.Error:
            pass
        inputfile.seek(0)
        reader = csvl10n.try_dialects(inputfile, self.fieldnames, self.dialect)
        first_row = True
        for row in reader:
            newce = self.UnitClass()
            newce.fromdict(row)
            if not first_row or not newce.match_header():
                self.addunit(newce)
            first_row = False


_sentences_from_unit_dispatch = {
    wordfast.WordfastUnit: sentences_from_wordfast_unit,
    csvl10n.csvunit: sentences_from_csv_unit,
    tmxunitl2: sentences_from_tmx_unit
}


def to_bitext(
        path: Path,
        source_langs: Union[LanguagePair, Tuple],
        replacements: Dict[str, str] = None,
        fieldnames: Tuple[str] = ('source', 'target'),
        **kw) -> Generator[Sentence, None, None]:
    """A generator `bitext` sentences from data in path `path`.

    Optional:

    `replacements`:

       Specify a mapping of character to replacement in
       `text_replacements`, to apply to items in the source data (e.g
       CSV row, XML tag) - by default - new-lines and tabs will be
       replaced with one 1 and 4 spaces respectively.

    Any keyword arguments are passed onto the relevant implementation.
    i.e: bitext_from_tmx or bitext_from_csv.
    """
    ext = os.path.splitext(path)[-1][1:]
    source_langs = LanguagePair(*source_langs)
    if ext in {'csv', 'txt'}:
        classes = None
    else:
        classes = dict(tmx=tmxfilel2, tsv=tsvfile)
    tm = factory.getobject(str(path), classes=classes)
    for unit in tm.unit_iter():
        sentence_producer = _sentences_from_unit_dispatch[type(unit)]
        sentences = sentence_producer(unit,
                                      source_langs,
                                      fieldnames=fieldnames)
        if sentences:
            yield tuple(sentences)


__all__ = ('Sentence',
           'normalize',
           'sentences_from_lang_data',
           'tmxfilel2',
           'tmxunitl2',
           'to_bitext',)
