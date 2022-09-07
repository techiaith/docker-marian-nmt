from collections import ChainMap
from functools import partial
from importlib import resources as ir
from itertools import repeat
from numbers import Number
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union
import io
import random
import shutil
import sys

from more_itertools import flatten
from techiaith.utils.bitext import LanguagePair, normalize
import jiwer
import sacrebleu
import sentencepiece as spm
import srsly

from . import templates
from .utils import commands, fs


DECODER_CONFIG_FILENAME = 'model.npz.best-bleu-detok.npz.decoder.yml'


def read_config_template() -> Dict:
    template = ir.read_text(templates, 'transformers.yml')
    return srsly.yaml_loads(template)


def _enumerated_line_map(fp):
    return dict((i, normalize(line.strip()))
                for (i, line) in enumerate(fp, start=1))


def write_combined_test_sets(
        src_path: Path,
        ref_path: Path,
        hyp_path: Path,
        out_path: Optional[Union[Path, io.BytesIO]] = None,
        n_samples: Optional[int] = 381
):
    if isinstance(out_path, (str, Path)):
        out_fp = fs.open_utf8(out_path, mode='w', encoding='utf-8')
    elif hasattr(out_path, 'write'):
        pass
    else:
        out_fp = sys.stdout
    with out_fp:
        with (fs.open_utf8(src_path) as src_fp,
              fs.open_utf8(ref_path) as ref_fp,
              fs.open_utf8(hyp_path) as hyp_fp):
            src_m = dict((text, i)
                         for (i, text) in _enumerated_line_map(src_fp).items())
            ref_m = _enumerated_line_map(ref_fp)
            hyp_m = _enumerated_line_map(hyp_fp)
            src_samples = random.sample(sorted(src_m), n_samples)
            for src_sample in src_samples:
                i = src_m[src_sample]
                (ref, hyp) = (ref_m[i], hyp_m[i])
                out_fp.write('-' * 80 + '\n')
                out_fp.write('\n')
                out_fp.write('SEGMENT: {:d}\n'.format(i))
                out_fp.write(f'src: {src_sample}\n')
                out_fp.write(f'ref: {ref}\n')
                out_fp.write(f'hyp: {hyp}\n')
                out_fp.write('\n')
                out_fp.write('REF PROBLEMUS:\n')
                out_fp.write('HYP PROBLEMUS:\n')
                out_fp.write('SYLW:\n')
                for _ in range(2):
                    out_fp.write('\n')
    return out_fp.name


def _sentence_iterator(paths):
    for path in paths:
        with fs.open_utf8(path) as fp:
            for line in fp:
                yield line.rstrip()


def get_vocab_path(langs: Union[LanguagePair, Tuple],
                   models_dir: Path) -> Path:
    vocab_filename = f'vocab.{langs.source}-{langs.target}.spm'
    return models_dir / vocab_filename


def create_spm_vocab(config_path: Path,
                     vocab_path: Path,
                     train_paths: List[Path]) -> Path:
    """Re-implementation of Marian NMT's SentencePiece vocab creation.

    Done in order to faciliate create a vocab for k-fold split corpora.

    Returns the path to the realized SentencePiece vocabulary model file.
    """
    # HARCODED parameters below have been copied verbatim from the
    # Marian NMT C++ code base or documentation.
    # Paramters mirror those hardcoded Marian C++ -
    # NB. Deviations to values of the *_id paramters cause CUDA memory
    # allocation issues.
    config = srsly.yaml_loads(config_path)
    dim_vocabs = config.get('dim-vocabs', [32000])
    max_lines = config.get('sentence-piece-max-lines', 2000000)
    max_size = max(dim_vocabs)
    spm_train = spm.SentencePieceTrainer.train
    sent_iter = _sentence_iterator(train_paths)
    spm_train(bos_id=-1,
              character_coverage=1.0,
              eos_id=0,
              input_sentence_size=max_lines,
              max_sentence_length=2048,
              model_prefix=vocab_path,
              sentence_iterator=sent_iter,
              unk_id=1,
              vocab_size=max_size)
    vocab_path.with_suffix(vocab_path.suffix + '.vocab').unlink()
    vocab_model = vocab_path.with_suffix(vocab_path.suffix + '.model')
    vocab_model.rename(vocab_path)
    return vocab_path


def configure(langs: Union[LanguagePair, Tuple],
              config_path: Path,
              vocab_path: Path) -> None:
    """Configure invariant Marian NMT settings training runs."""
    langs = LanguagePair(*langs)
    config = read_config_template()
    vocabs = list(repeat(str(vocab_path), len(langs)))
    config['vocabs'] = vocabs
    with fs.open_utf8(config_path, 'w') as fp:
        fp.write(srsly.yaml_dumps(config))


def train(langs: Union[LanguagePair, Tuple],
          config_path: Path,
          model: Path,
          log: Path,
          valid_log: Path,
          valid_translation_output: Path,
          train_sets: Tuple[Path],
          valid_sets: Tuple[Path]):
    """Run Marian NMT training with YAML configuration file `config`."""
    langs = LanguagePair(*langs)
    extra_config = {
        '--log': str(log),
        '--valid-log': str(valid_log),
        '--model': str(model),
        '--train-sets': ' '.join(map(str, train_sets)),
        '--valid-sets': ' '.join(map(str, valid_sets)),
        '--valid-translation-output': str(valid_translation_output),
    }
    cmd_args = ['marian', '-c', str(config_path)]
    cmd_args.extend(list(flatten(extra_config.items())))
    cmd = ' '.join(list(cmd_args))
    commands.run(cmd)


def sacrebleu_scores(hypothosis: Sequence[str],
                     references: Sequence[str]) -> Dict:
    scores = {}
    metrics = ('BLEU', 'CHRF', 'TER')
    for metric_name in metrics:
        metric_cls = getattr(sacrebleu, metric_name)
        metric = metric_cls()
        score = metric.corpus_score(hypothosis, references)
        sig = metric.get_signature()
        detailed = dict(score=score, signature=sig)
        scores[metric_name] = dict(score=score.score, detail=detailed)
    return scores


def run_decoder(langs: LanguagePair,
                decoder_config: Path,
                input_path: Path,
                output_path: Path,
                log: Path,
                model: Path) -> None:
    cmd_args = [
        'marian-decoder',
        '--beam-size', '6',
        '--config', decoder_config,
        '--input', input_path,
        '--log', log,
        '--maxi-batch', '100',
        '--maxi-batch-sort', 'src',
        '--mini-batch', '64',
        '--models', model,
        '--normalize', '0.6',
        '--output', output_path,
        '--workspace', '6000'
    ]
    cmd = ' '.join(map(str, cmd_args))
    commands.run(cmd)


def _trg_lang_path_with_suffix(path, ident, langs, ext):
    path = path.with_suffix(f'.{langs.target}.' + ext)
    path = path.parent / ident / path.name
    fs.ensure_folders_exist(path.parent)
    return path


def calculate_error_rates(hypothosis: List[str],
                          references: List[str]) -> Dict[str, Number]:
    """Calculate WER, MER and WIL metrics."""
    measures = jiwer.compute_measures(references, hypothosis)
    return {k: dict(score=measures[k.lower()])
            for k in ('WER', 'MER', 'WIL')}


def score(langs: LanguagePair,
          models_dir: Path,
          work_dir: Path,
          log: Path,
          vt_out: Path,
          num_combined_samples: Optional[int] = 381,
          test_set_prefix: str = 'corpus.test') -> Dict:
    """Obtain scores from the current training run.

    SacreBLEU is used to compute BLEU, CHRF and TER scores.

    Temporary files will be saved to `work_dir` containing the
    "reference" and "hypothosis" data passed to the sacreBLEU scoring
    function.

    Returns the result of `sacrebleu.BLEU.corpus_score(ref, hyp)`.
    """
    split_subdir = models_dir.stem
    trg_ref_path = work_dir / f'{test_set_prefix}.{langs.target}'
    target_path = partial(_trg_lang_path_with_suffix,
                          trg_ref_path,
                          split_subdir,
                          langs)
    ref_path = target_path('ref')
    hyp_path = target_path('hyp')
    decoder_config = models_dir / DECODER_CONFIG_FILENAME
    input_path = work_dir / f'{test_set_prefix}.{langs.source}'
    output_filename = input_path.stem + f'.{langs.target}.output'
    output_path = work_dir / split_subdir / output_filename
    model = models_dir / 'model.npz.best-bleu-detok.npz'
    is_decoded = all(path.exists() for path in (trg_ref_path, output_path))
    if not is_decoded:
        run_decoder(langs, decoder_config, input_path, output_path, log, model)
        shutil.copy(trg_ref_path, ref_path)
        shutil.copy(output_path, hyp_path)
    references = fs.readlines(trg_ref_path)
    hypothosis = fs.readlines(output_path)
    comb_out_name = f'{langs.target}.src-ref-hyp_combined.txt'
    comb_out_path = ref_path.with_name(comb_out_name)
    write_combined_test_sets(input_path, ref_path, hyp_path, comb_out_path)
    scores = sacrebleu_scores(hypothosis, [references])
    error_rates = calculate_error_rates(hypothosis, references)
    return ChainMap(scores, error_rates)
